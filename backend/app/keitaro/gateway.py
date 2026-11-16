# backend/app/keitaro/gateway.py

import re
import logging
from app.models import Campaign, Stream
from app.keitaro.client import KeitaroClient

log = logging.getLogger(__name__)


class KeitaroGateway:
    def __init__(self, client: KeitaroClient):
        self.client = client

    def _campaign_payload(self, c: Campaign) -> dict:
        alias = re.sub(r"[^a-zA-Z0-9_-]", "-", c.name).lower()
        alias = f"{alias}-{str(c.id)[:8]}"
        return {
            "alias": alias,
            "name": c.name
        }

    def _stream_payload(self, s: Stream, campaign: Campaign) -> dict:
        if s.type == "redirect":
            filters = []
            if campaign.geo_code:
                filters.append({
                    "name": "country",
                    "mode": "accept",
                    "payload": [campaign.geo_code],
                })

            return {
                "campaign_id": campaign.keitaro_campaign_id,
                "name": f"Redirect to Google ({campaign.geo_code})",
                "type": "regular",
                "schema": "redirect",
                "action_type": "http",
                "action_payload": s.redirect_url,
                "weight": 100,
                "position": s.position,
                "state": "active",
                "collect_clicks": True,
                "filter_or": False,
                "filters": filters,
            }

        return {
            "campaign_id": campaign.keitaro_campaign_id,
            "name": f"Offers flow #{s.position}",
            "type": "regular",
            "schema": "landings",
            "action_type": "campaign",
            "weight": 100,
            "position": s.position,
            "state": "active",
            "collect_clicks": True,
            "filter_or": False,
            "filters": [],
            "offers": [
                {
                    "offer_id": int(o.keitaro_offer_id),
                    "share": int(o.weight),
                    "state": "active",
                }
                for o in s.offers if not o.is_deleted_in_kt
            ],
        }

    async def push_campaign(self, c: Campaign) -> tuple[int, dict[int, int]]:
        """
        Возвращает (keitaro_campaign_id, {our_stream_id: keitaro_stream_id}).
        """
        if c.keitaro_campaign_id is None:
            kt_campaign_id = await self.client.create_campaign(self._campaign_payload(c))
            c.keitaro_campaign_id = kt_campaign_id
        else:
            kt_campaign_id = c.keitaro_campaign_id

        stream_ids: dict[int, int] = {}
        for s in c.streams:
            payload = self._stream_payload(s, c)
            log.info("Pushing stream %s: %s", s.id, payload)

            if s.keitaro_stream_id is None:
                kt_sid = await self.client.create_stream(payload)
            else:
                await self.client.update_stream(kt_campaign_id, s.keitaro_stream_id, payload)
                kt_sid = s.keitaro_stream_id
            stream_ids[s.id.int] = kt_sid

        return kt_campaign_id, stream_ids