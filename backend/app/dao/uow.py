from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.dao.campaign_dao import CampaignDAO
from app.dao.stream_dao import StreamDAO
from app.dao.version_dao import VersionDAO
from app.dao.push_log_dao import PushLogDAO


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._sf = session_factory

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._sf()
        self.campaigns = CampaignDAO(self.session)
        self.streams = StreamDAO(self.session)
        self.versions = VersionDAO(self.session)
        self.push_logs = PushLogDAO(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
