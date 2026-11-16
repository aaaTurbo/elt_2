from app.keitaro.offer_catalog import OfferCatalog


class OfferCatalogService:
    def __init__(self, catalog: OfferCatalog):
        self.catalog = catalog

    async def search(self, q: str, limit: int = 20) -> list[dict]:
        return await self.catalog.search(q, limit)

    async def refresh(self) -> int:
        return await self.catalog.refresh()
