from sqlalchemy.ext.asyncio import AsyncSession
from app.models import KeitaroPushLog


class PushLogDAO:
    def __init__(self, session: AsyncSession):
        self.s = session

    def add(self, log: KeitaroPushLog) -> None:
        self.s.add(log)
