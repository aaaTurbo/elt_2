from fastapi import APIRouter, Depends, Query
from app.api.deps import get_offer_catalog_service
from app.services.offer_catalog_service import OfferCatalogService

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("/search")
async def search_offers(
    q: str = Query("", max_length=100),
    limit: int = Query(20, ge=1, le=100),
    svc: OfferCatalogService = Depends(get_offer_catalog_service),
):
    """
    Поиск офферов по id или имени (case-insensitive substring).
    Используется для autocomplete в UI.
    """
    return await svc.search(q, limit)


@router.post("/refresh")
async def refresh_offers(
    svc: OfferCatalogService = Depends(get_offer_catalog_service),
):

    count = await svc.refresh()
    return {"ok": True, "count": count}
