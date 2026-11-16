import uuid
import logging
from app.dao.uow import UnitOfWork
from app.exceptions import KeitaroError, NotFoundError
from app.keitaro.gateway import KeitaroGateway
from app.models import CampaignVersion, KeitaroPushLog, EditSession

log = logging.getLogger(__name__)


class PushService:
    def __init__(self, uow: UnitOfWork, gateway: KeitaroGateway):
        self.uow = uow
        self.gateway = gateway

    async def push(self, campaign_id: uuid.UUID) -> dict:
        c = await self.uow.campaigns.get(campaign_id)
        if not c:
            raise NotFoundError("Campaign not found")

        session = await self.uow.campaigns.active_draft_session(campaign_id)
        if session is None:
            session = EditSession(campaign_id=campaign_id, status="draft")
            self.uow.campaigns.add_session(session)
            await self.uow.session.flush()

        c = await self.uow.campaigns.get_with_streams(campaign_id)

        streams = c.streams

        log_rec = KeitaroPushLog(
            campaign_id=c.id,
            edit_session_id=session.id,
            idempotency_key=str(uuid.uuid4()),
            payload={},
            status="pending",
        )
        self.uow.push_logs.add(log_rec)
        await self.uow.session.flush()

        payload_snapshot = self._snapshot(c, streams)
        log_rec.payload = payload_snapshot

        try:
            log.info("PUSH STEP 1: creating campaign %s", c.id)
            kt_cid, kt_stream_ids = await self.gateway.push_campaign(c)
        except Exception as e:
            log.error("PUSH FAILED on campaign/streams: %s", e, exc_info=True)
            log_rec.status = "failed"
            log_rec.error = str(e)
            session.status = "failed"
            await self.uow.commit()
            raise KeitaroError(f"Push failed: {e}") from e

        c.keitaro_campaign_id = kt_cid
        for s in streams:
            if s.id.int in kt_stream_ids:
                s.keitaro_stream_id = kt_stream_ids[s.id.int]

        version_number = await self.uow.versions.next_version_number(c.id)
        version = CampaignVersion(
            campaign_id=c.id,
            version_number=version_number,
            snapshot=payload_snapshot,
        )
        self.uow.versions.add(version)
        c.current_version_number = version_number

        log_rec.status = "success"
        log_rec.response = {"keitaro_campaign_id": kt_cid}
        session.status = "published"

        await self.uow.commit()
        return {
            "keitaro_campaign_id": kt_cid,
            "version_number": version_number,
        }

    def _snapshot(self, c, streams) -> dict:
        return {
            "campaign": {
                "name": c.name,
                "geo_code": c.geo_code,
                "domain": c.domain,
                "group_id": c.group_id,
                "source_id": c.source_id,
            },
            "streams": [
                {
                    "type": s.type,
                    "redirect_url": s.redirect_url,
                    "position": s.position,
                    "offers": [
                        {
                            "keitaro_offer_id": o.keitaro_offer_id,
                            "weight": float(o.weight),
                            "is_weight_fixed": o.is_weight_fixed,
                            "is_deleted_in_kt": o.is_deleted_in_kt,
                        }
                        for o in s.offers
                    ],
                }
                for s in streams
            ],
        }
