import asyncio
from datetime import datetime, timedelta
from app.keitaro.client import KeitaroClient


class OfferCatalog:
    """
    In-memory TTL-кэш офферов Keitaro.
    Лениво загружается при первом поиске и обновляется по истечении TTL.
    """

    def __init__(self, client: KeitaroClient, ttl_seconds: int = 300):
        self.client = client
        self.ttl = timedelta(seconds=ttl_seconds)
        self._items: list[dict] = []
        self._loaded_at: datetime | None = None
        self._lock = asyncio.Lock()

    def _is_fresh(self) -> bool:
        return (
            self._loaded_at is not None
            and (datetime.utcnow() - self._loaded_at) < self.ttl
        )

    async def _ensure_loaded(self, force: bool = False) -> None:
        if not force and self._is_fresh():
            return
        async with self._lock:
            if not force and self._is_fresh():
                return
            items = await self.client.list_offers()
            self._items = items
            self._loaded_at = datetime.utcnow()

    async def search(self, q: str, limit: int = 20) -> list[dict]:
        await self._ensure_loaded()
        q_norm = (q or "").strip().lower()
        if not q_norm:
            return self._items[:limit]
        result = []
        for o in self._items:
            if q_norm in str(o["id"]) or q_norm in o["name"].lower():
                result.append(o)
                if len(result) >= limit:
                    break
        return result

    async def refresh(self) -> int:
        await self._ensure_loaded(force=True)
        return len(self._items)
