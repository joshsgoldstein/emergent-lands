from sqlalchemy import text

import pytest
from emergent.db.connection import DatabaseManager, get_database_url


def _db_url(test_db_engine):
    return test_db_engine.url.render_as_string(hide_password=False)


def test_get_database_url_default():
    url = get_database_url()
    assert "postgresql+asyncpg://" in url


def test_get_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host:5432/mydb")
    url = get_database_url()
    assert url == "postgresql+asyncpg://user:pass@host:5432/mydb"


@pytest.mark.asyncio
async def test_database_manager_init_and_close(test_db_engine):
    mgr = DatabaseManager(_db_url(test_db_engine))
    await mgr.initialize()
    assert mgr.engine is not None
    assert mgr.session_factory is not None
    await mgr.close()
    assert mgr.engine is None


@pytest.mark.asyncio
async def test_database_manager_session(test_db_engine):
    mgr = DatabaseManager(_db_url(test_db_engine))
    await mgr.initialize()
    from emergent.db.base import Base

    async with mgr.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with mgr.session() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    await mgr.close()
