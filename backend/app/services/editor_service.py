import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.dao.uow import UnitOfWork
from app.domain.weight_allocator import WeightAllocator
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import Campaign, EditSession, Stream, StreamOffer


class EditorService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.allocator = WeightAllocator()

    async def _ensure_draft(self, campaign: Campaign) -> EditSession:
        session = await self.uow.campaigns.active_draft_session(campaign.id)
        if session is None:
            session = EditSession(campaign_id=campaign.id, status="draft")
            self.uow.campaigns.add_session(session)
            await self.uow.session.flush()
        return session

    async def discard(self, campaign_id: uuid.UUID, kt_client) -> dict:
        session = await self.uow.campaigns.active_draft_session(campaign_id)
        if session is not None:
            await self.uow.session.delete(session)
            await self.uow.session.flush()

        c = await self._get_campaign(campaign_id)
        if c.keitaro_campaign_id is not None:
            return await self.fetch_from_kt(campaign_id, kt_client)

        return await self.get_state(campaign_id)

    async def get_state(self, campaign_id: uuid.UUID) -> dict:
        c = await self.uow.campaigns.get_with_streams(campaign_id)
        if not c:
            raise NotFoundError("Campaign not found")
        streams = await self.uow.streams.by_campaign(campaign_id)

        try:
            from app.api.deps import get_offer_catalog
            catalog = get_offer_catalog()
            offers_list = await catalog.search("", limit=1000)
            name_map = {o["id"]: o["name"] for o in offers_list}

            for s in streams:
                for o in s.offers:
                    if not o.name and o.keitaro_offer_id in name_map:
                        o.name = name_map[o.keitaro_offer_id]
        except Exception:
            pass

        session = await self.uow.campaigns.active_draft_session(campaign_id)
        res = self._serialize(c, streams)
        res["has_draft"] = session is not None
        return res

    def _serialize(self, c: Campaign, streams: list[Stream]) -> dict:
        return {
            "campaign": {
                "id": str(c.id),
                "name": c.name,
                "geo_code": c.geo_code,
                "domain": c.domain,
                "group_id": c.group_id,
                "source_id": c.source_id,
                "keitaro_campaign_id": c.keitaro_campaign_id,
                "current_version_number": c.current_version_number,
            },
            "streams": [
                {
                    "id": str(s.id),
                    "type": s.type,
                    "redirect_url": s.redirect_url,
                    "keitaro_stream_id": s.keitaro_stream_id,
                    "position": s.position,
                    "offers": [
                        {
                            "id": str(o.id),
                            "keitaro_offer_id": o.keitaro_offer_id,
                            "name": o.name,
                            "weight": float(o.weight),
                            "is_weight_fixed": o.is_weight_fixed,
                            "is_deleted_in_kt": o.is_deleted_in_kt,
                            "deleted_in_kt_at": o.deleted_in_kt_at.isoformat()
                            if o.deleted_in_kt_at else None,
                        }
                        for o in s.offers
                    ],
                }
                for s in streams
            ],
        }

    async def add_offer(
        self, campaign_id: uuid.UUID, stream_id: uuid.UUID, keitaro_offer_id: int, name: str | None
    ) -> dict:
        c = await self._get_campaign(campaign_id)
        s = await self._get_stream(campaign_id, stream_id)
        if s.type != "flow":
            raise ValidationError("Can only add offers to a 'flow' stream")
        await self._ensure_draft(c)

        offer = StreamOffer(
            stream_id=s.id,
            name=name,
            keitaro_offer_id=keitaro_offer_id,
            weight=Decimal("0"),
        )
        self.uow.streams.add_offer(offer)
        await self.uow.session.flush()

        all_offers = await self._reload_offers(stream_id)
        self.allocator.allocate_for_new(all_offers, offer)

        await self.uow.commit()
        return await self.get_state(campaign_id)

    async def remove_offer(
            self, campaign_id: uuid.UUID, stream_id: uuid.UUID, offer_row_id: uuid.UUID
    ) -> dict:
        c = await self._get_campaign(campaign_id)
        offer = await self.uow.streams.get_offer(stream_id, offer_row_id)
        if offer is None:
            raise NotFoundError("Offer not found")
        if offer.is_deleted_in_kt:
            raise ConflictError("Offer already marked as deleted.")

        await self._ensure_draft(c)

        offer.is_deleted_in_kt = True
        offer.deleted_in_kt_at = datetime.now(timezone.utc)

        await self.uow.session.flush()

        remaining = await self._reload_offers(stream_id)
        if remaining:
            self.allocator.recalculate(remaining)

        await self.uow.commit()
        return await self.get_state(campaign_id)

    async def rollback_offer(
        self, campaign_id: uuid.UUID, stream_id: uuid.UUID, offer_row_id: uuid.UUID
    ) -> dict:
        c = await self._get_campaign(campaign_id)
        offer = await self.uow.streams.get_offer(stream_id, offer_row_id)
        if offer is None:
            raise NotFoundError("Offer not found")
        if not offer.is_deleted_in_kt:
            raise ConflictError("Offer is not marked as deleted-in-KT")
        await self._ensure_draft(c)

        offer.is_deleted_in_kt = False
        offer.deleted_in_kt_at = None
        offer.weight = Decimal("0")

        all_offers = await self._reload_offers(stream_id)
        self.allocator.allocate_for_new(all_offers, offer)

        await self.uow.commit()
        return await self.get_state(campaign_id)

    async def set_fixed(
        self,
        campaign_id: uuid.UUID,
        stream_id: uuid.UUID,
        offer_row_id: uuid.UUID,
        fixed: bool,
        weight: float | None = None,
    ) -> dict:
        c = await self._get_campaign(campaign_id)
        offer = await self.uow.streams.get_offer(stream_id, offer_row_id)
        if offer is None:
            raise NotFoundError("Offer not found")
        if offer.is_deleted_in_kt:
            raise ConflictError("Cannot modify a deleted-in-KT offer")
        await self._ensure_draft(c)

        if fixed:
            if weight is not None:
                offer.weight = Decimal(str(weight))
            offer.is_weight_fixed = True
        else:
            offer.is_weight_fixed = False

        offers = await self._reload_offers(stream_id)
        self.allocator.recalculate(offers)

        await self.uow.commit()
        return await self.get_state(campaign_id)

    async def _get_campaign(self, cid: uuid.UUID) -> Campaign:
        c = await self.uow.campaigns.get(cid)
        if not c:
            raise NotFoundError("Campaign not found")
        return c

    async def _get_stream(self, cid: uuid.UUID, sid: uuid.UUID) -> Stream:
        s = await self.uow.streams.get(sid)
        if not s or s.campaign_id != cid:
            raise NotFoundError("Stream not found")
        return s

    async def _reload_offers(self, stream_id: uuid.UUID) -> list[StreamOffer]:
        s = await self.uow.streams.get(stream_id)
        assert s is not None
        return s.offers

    async def fetch_from_kt(self, campaign_id: uuid.UUID, kt_client) -> dict:

        c = await self._get_campaign(campaign_id)
        if c.keitaro_campaign_id is None:
            raise ConflictError("Campaign has not been pushed to Keitaro yet")

        streams_raw = await kt_client.get_campaign_streams(c.keitaro_campaign_id)
        kt_streams = {int(s["id"]): s for s in streams_raw}

        streams = await self.uow.streams.by_campaign(campaign_id)
        for s in streams:
            if s.keitaro_stream_id is None:
                continue

            kt_s = kt_streams.get(s.keitaro_stream_id)
            if not kt_s:
                continue

            kt_offers: dict[int, dict] = {}
            for o in kt_s.get("offers", []):
                if o.get("offer_id") is not None and o.get("state", "active") == "active":
                    kt_offers[int(o["offer_id"])] = o

            existing_kt_ids: set[int] = set()

            for o in s.offers:
                existing_kt_ids.add(o.keitaro_offer_id)
                if o.keitaro_offer_id in kt_offers:
                    o.is_deleted_in_kt = False
                    o.deleted_in_kt_at = None

                    kt_offer = kt_offers[o.keitaro_offer_id]
                    share = kt_offer.get("share")
                    if share is not None:
                        o.weight = Decimal(str(share))
                else:
                    o.is_deleted_in_kt = True
                    if not o.deleted_in_kt_at:
                        o.deleted_in_kt_at = datetime.now(timezone.utc)
                    o.weight = Decimal("0")

            for kt_offer_id, kt_offer in kt_offers.items():
                if kt_offer_id not in existing_kt_ids:
                    share = kt_offer.get("share", 0)
                    new_offer = StreamOffer(
                        stream_id=s.id,
                        keitaro_offer_id=kt_offer_id,
                        name=kt_offer.get("name"),
                        weight=Decimal(str(share)),
                        is_deleted_in_kt=False,
                    )
                    self.uow.streams.add_offer(new_offer)

        await self.uow.commit()
        return await self.get_state(campaign_id)

