import os
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://emergent:emergent_dev@localhost:5432/emergent_lands",
    )


class DatabaseManager:
    def __init__(self, database_url: Optional[str] = None):
        self._database_url = database_url or get_database_url()
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def initialize(self, echo: bool = False):
        self.engine = create_async_engine(self._database_url, echo=echo)
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    def session(self) -> AsyncSession:
        if self.session_factory is None:
            raise RuntimeError("DatabaseManager not initialized")
        return self.session_factory()
