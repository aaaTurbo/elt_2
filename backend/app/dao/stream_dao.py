import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models import Stream, StreamOffer


class StreamDAO:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def by_campaign(self, cid: uuid.UUID) -> list[Stream]:
        stmt = (
            select(Stream)
            .where(Stream.campaign_id == cid)
            .options(selectinload(Stream.offers))
            .order_by(Stream.position)
        )
        return list((await self.s.execute(stmt)).scalars())

    async def get(self, sid: uuid.UUID) -> Stream | None:
        stmt = select(Stream).where(Stream.id == sid).options(selectinload(Stream.offers))
        return (await self.s.execute(stmt)).scalar_one_or_none()

    async def get_offer(self, sid: uuid.UUID, offer_row_id: uuid.UUID) -> StreamOffer | None:
        stmt = select(StreamOffer).where(
            StreamOffer.id == offer_row_id, StreamOffer.stream_id == sid
        )
        return (await self.s.execute(stmt)).scalar_one_or_none()

    def add(self, s: Stream) -> None:
        self.s.add(s)

    def delete(self, s: Stream) -> None:
        self.s.delete(s)

    def add_offer(self, o: StreamOffer) -> None:
        self.s.add(o)

    def delete_offer(self, o: StreamOffer) -> None:
        self.s.delete(o)
