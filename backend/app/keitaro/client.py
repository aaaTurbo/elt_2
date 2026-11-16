import logging
import httpx
from app.config import settings

log = logging.getLogger(__name__)


class KeitaroClient:
    """
    Тонкий HTTP-клиент Keitaro Admin API. В mock-режиме имитирует KT.
    """

    def __init__(self, mock: bool | None = None):
        self.mock = settings.keitaro_mock if mock is None else mock
        self._counter = 1000

    def _next_id(self) -> int:
        self._counter += 1
        return self._counter

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        if self.mock:
            log.info("Keitaro MOCK %s %s", method, path)
            return {"ok": True, "mock": True}

        url = f"{settings.keitaro_api_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Api-Key": settings.keitaro_api_key}

        log.info("Keitaro REQUEST %s %s json=%s", method, path, kwargs.get("json"))

        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.request(method, url, headers=headers, **kwargs)

            if r.status_code >= 400:
                log.error("Keitaro ERROR status=%s body=%s", r.status_code, r.text)
                raise RuntimeError(f"Keitaro API {r.status_code}: {r.text}")

            return r.json()

    async def list_offers(self) -> list[dict]:
        """
        Возвращает список всех офферов из KT (пагинация).
        Формат: [{"id": int, "name": str}, ...]
        """
        if self.mock:
            return [
                {"id": 101, "name": "Lead Gen DE - Premium"},
                {"id": 102, "name": "Crypto Trial US - SOI"},
                {"id": 103, "name": "Dating FR - CPL"},
                {"id": 104, "name": "Finance UK - RevShare"},
                {"id": 105, "name": "Gaming CA - CPA"},
                {"id": 106, "name": "Sweeps AU"},
                {"id": 107, "name": "Insurance ES - PPL"},
                {"id": 108, "name": "Nutra BR - Trial"},
            ]

        results: list[dict] = []
        offset = 0
        limit = 200
        while True:
            data = await self._request(
                "GET", "offers", params={"limit": limit, "offset": offset}
            )
            items = data.get("items", data) if isinstance(data, dict) else data
            if not items:
                break
            for o in items:
                results.append({"id": int(o["id"]), "name": o.get("name", "")})
            if len(items) < limit:
                break
            offset += limit
        return results

    async def create_campaign(self, payload: dict) -> int:
        if self.mock:
            return self._next_id()
        data = await self._request("POST", "campaigns", json=payload)
        return int(data["id"])

    async def create_stream(self, payload: dict) -> int:
        if self.mock:
            return self._next_id()
        data = await self._request("POST", "streams", json=payload)
        return int(data["id"])

    async def update_stream(self, campaign_id: int, stream_id: int, payload: dict) -> None:
        if self.mock:
            return
        await self._request("PUT", f"streams/{stream_id}", json=payload)

    async def delete_stream(self, campaign_id: int, stream_id: int) -> None:
        if self.mock:
            return
        await self._request(
            "DELETE", f"campaigns/{campaign_id}/streams/{stream_id}"
        )

    async def get_campaign(self, campaign_id: int) -> dict:
        if self.mock:
            return {"id": campaign_id, "streams": []}
        return await self._request("GET", f"campaigns/{campaign_id}")

    async def get_campaign_streams(self, campaign_id: int) -> list[dict]:
        if self.mock:
            return []
        data = await self._request("GET", f"campaigns/{campaign_id}/streams")
        if isinstance(data, dict):
            return data.get("items", data.get("streams", []))
        return data if isinstance(data, list) else []
