from typing import AsyncIterator
from fastapi import Depends
from functools import lru_cache
from app.database import SessionFactory
from app.dao.uow import UnitOfWork
from app.keitaro.client import KeitaroClient
from app.keitaro.gateway import KeitaroGateway
from app.keitaro.offer_catalog import OfferCatalog
from app.services.offer_catalog_service import OfferCatalogService
from app.services.campaign_service import CampaignService
from app.services.editor_service import EditorService
from app.services.push_service import PushService

@lru_cache
def get_offer_catalog() -> OfferCatalog:
    return OfferCatalog(KeitaroClient(), ttl_seconds=300)


def get_offer_catalog_service() -> OfferCatalogService:
    return OfferCatalogService(get_offer_catalog())

async def get_uow() -> AsyncIterator[UnitOfWork]:
    async with UnitOfWork(SessionFactory) as uow:
        yield uow


def get_kt_client() -> KeitaroClient:
    return KeitaroClient()


def get_campaign_service(uow: UnitOfWork = Depends(get_uow)) -> CampaignService:
    return CampaignService(uow)


def get_editor_service(uow: UnitOfWork = Depends(get_uow)) -> EditorService:
    return EditorService(uow)


def get_push_service(
    uow: UnitOfWork = Depends(get_uow),
    client: KeitaroClient = Depends(get_kt_client),
) -> PushService:
    return PushService(uow, KeitaroGateway(client))
