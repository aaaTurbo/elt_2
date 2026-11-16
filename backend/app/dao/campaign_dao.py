import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models import Campaign, EditSession


class CampaignDAO:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def get(self, cid: uuid.UUID) -> Campaign | None:
        return await self.s.get(Campaign, cid)

    async def get_with_streams(self, cid: uuid.UUID) -> Campaign | None:
        stmt = (
            select(Campaign)
            .where(Campaign.id == cid)
        )
        return (await self.s.execute(stmt)).unique().scalar_one_or_none()

    async def list(self) -> list[Campaign]:
        return list((await self.s.execute(select(Campaign).order_by(Campaign.created_at.desc()))).scalars())

    def add(self, c: Campaign) -> None:
        self.s.add(c)

    async def active_draft_session(self, cid: uuid.UUID) -> EditSession | None:
        stmt = (
            select(EditSession)
            .where(EditSession.campaign_id == cid, EditSession.status == "draft")
            .order_by(EditSession.created_at.desc())
            .limit(1)
        )
        return (await self.s.execute(stmt)).scalar_one_or_none()

    def add_session(self, s: EditSession) -> None:
        self.s.add(s)
