import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models import CampaignVersion


class VersionDAO:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def list_for_campaign(self, cid: uuid.UUID) -> list[CampaignVersion]:
        stmt = (
            select(CampaignVersion)
            .where(CampaignVersion.campaign_id == cid)
            .order_by(CampaignVersion.version_number.desc())
        )
        return list((await self.s.execute(stmt)).scalars())

    async def next_version_number(self, cid: uuid.UUID) -> int:
        stmt = select(func.max(CampaignVersion.version_number)).where(
            CampaignVersion.campaign_id == cid
        )
        current = (await self.s.execute(stmt)).scalar()
        return (current or 0) + 1

    def add(self, v: CampaignVersion) -> None:
        self.s.add(v)
