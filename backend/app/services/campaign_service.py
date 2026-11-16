import uuid
from decimal import Decimal
from app.dao.uow import UnitOfWork
from app.exceptions import NotFoundError
from app.models import Campaign, Stream, StreamOffer
from app.config import settings


class CampaignService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create(
        self,
        name: str,
        geo_code: str,
        offer_id: int,
        offer_name: str | None = None,
        domain: str | None = None,
        group_id: int | None = None,
        source_id: int | None = None,
    ) -> Campaign:
        c = Campaign(
            name=name,
            geo_code=geo_code.upper(),
            domain=domain or settings.keitaro_domain_default,
            group_id=group_id or settings.keitaro_group_id_default,
            source_id=source_id or settings.keitaro_source_id_default,
        )
        s = Stream(campaign=c, type="flow", position=1)
        StreamOffer(
            stream=s,
            keitaro_offer_id=offer_id,
            name=offer_name,
            weight=Decimal("100.00"),
        )
        self.uow.campaigns.add(c)
        await self.uow.commit()
        return c

    async def list(self) -> list[Campaign]:
        return await self.uow.campaigns.list()

    async def get(self, cid: uuid.UUID) -> Campaign:
        c = await self.uow.campaigns.get_with_streams(cid)
        if not c:
            raise NotFoundError(f"Campaign {cid} not found")
        return c
