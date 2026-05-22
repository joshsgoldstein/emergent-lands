# Week 1: Project Scaffold & Core Systems

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundation of emergent-lands: an installable Python package with PostgreSQL persistence, LLM provider abstraction, OpenAI integration, and a tool registry with 12 core tools — all running in Docker Compose.

**Architecture:** FastAPI-based async Python application with SQLAlchemy + asyncpg for PostgreSQL, a provider-agnostic LLM abstraction layer, and a three-tier tool system (core → location-gated → agent-gated). Everything is containerized: one service for the app, one for PostgreSQL, sharing a Docker network.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 + asyncpg, Alembic, OpenAI SDK, Pydantic, Docker Compose, pytest + pytest-asyncio

---

### Task 1: pyproject.toml + Package Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `emergent/__init__.py`
- Create: `emergent/cli/__init__.py`
- Create: `emergent/engine/__init__.py`
- Create: `emergent/agents/__init__.py`
- Create: `emergent/models/__init__.py`
- Create: `emergent/tools/__init__.py`
- Create: `emergent/tools/locations/__init__.py`
- Create: `emergent/tools/agent/__init__.py`
- Create: `emergent/world/__init__.py`
- Create: `emergent/db/__init__.py`
- Create: `emergent/api/__init__.py`

- [ ] **Step 1: Create pyproject.toml with all dependencies**

```toml
[project]
name = "emergent-lands"
version = "0.1.0"
description = "A persistent world where autonomous AI agents live, govern, and evolve"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "openai>=1.50.0",
    "anthropic>=0.40.0",
    "google-genai>=1.0.0",
    "pyyaml>=6.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "click>=8.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.6.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100

[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["emergent*"]
```

- [ ] **Step 2: Create package directory structure and __init__.py files**

Run:
```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
mkdir -p emergent/{cli,engine,agents,models,tools/{locations,agent},world,db,api}
mkdir -p tests
mkdir -p config/{worlds,landmarks}
# Create all __init__.py files with a version string
for dir in emergent emergent/cli emergent/engine emergent/agents emergent/models emergent/tools emergent/tools/locations emergent/tools/agent emergent/world emergent/db emergent/api; do
    echo "from importlib.metadata import version" > "$dir/__init__.py"
    echo "" >> "$dir/__init__.py"
    echo '__version__ = version("emergent-lands")' >> "$dir/__init__.py"
done
```

Expected output: All directories and `__init__.py` files created, `pip install -e ".[dev]"` succeeds.

- [ ] **Step 3: Install the package and verify**

Run:
```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pip install -e ".[dev]"
python -c "import emergent; print(emergent.__version__)"
```

Expected: prints `0.1.0`

- [ ] **Step 4: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands init
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add pyproject.toml emergent/ tests/ config/
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "chore: scaffold pyproject.toml and package skeleton"
```

---

### Task 2: Docker Compose Setup

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yaml`
- Create: `.dockerignore`
- Create: `.env.example`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dist --upgrade pip

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY emergent/ emergent/
COPY config/ config/

CMD ["python", "-m", "emergent.cli.run"]
```

- [ ] **Step 2: Create docker-compose.yaml with PostgreSQL + app service on isolated network**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: emergent
      POSTGRES_PASSWORD: emergent_dev
      POSTGRES_DB: emergent_lands
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U emergent -d emergent_lands"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - emergent-net

  app:
    build: .
    command: emergence run --world /app/config/worlds/mvp.yaml --duration 48
    environment:
      DATABASE_URL: postgresql+asyncpg://emergent:emergent_dev@db:5432/emergent_lands
    volumes:
      - ./emergent:/app/emergent
      - ./config:/app/config
    depends_on:
      db:
        condition: service_healthy
    networks:
      - emergent-net
    profiles:
      - production

  app-dev:
    build: .
    command: tail -f /dev/null
    environment:
      DATABASE_URL: postgresql+asyncpg://emergent:emergent_dev@db:5432/emergent_lands
    volumes:
      - ./emergent:/app/emergent
      - ./config:/app/config
      - ./tests:/app/tests
    depends_on:
      db:
        condition: service_healthy
    networks:
      - emergent-net
    profiles:
      - dev

volumes:
  pgdata:

networks:
  emergent-net:
    driver: bridge
```

- [ ] **Step 3: Create .dockerignore and .env.example**

```gitignore
# .dockerignore
__pycache__
*.pyc
.git
.venv
.env
*.egg-info
```

```bash
# .env.example
DATABASE_URL=postgresql+asyncpg://emergent:emergent_dev@localhost:5432/emergent_lands
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

- [ ] **Step 4: Add .gitignore**

```gitignore
__pycache__/
*.pyc
.env
*.egg-info/
.venv/
.pytest_cache/
```

- [ ] **Step 5: Verify Docker Compose starts PostgreSQL**

Run:
```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
docker compose up -d db
docker compose logs db --tail 20
```

Expected: PostgreSQL starts, `pg_isready` returns `accepting connections`.

- [ ] **Step 6: Cleanup**

```bash
docker compose down -v
```

- [ ] **Step 7: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add Dockerfile docker-compose.yaml .dockerignore .gitignore .env.example
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add Docker Compose with PostgreSQL and app service"
```

---

### Task 3: SQLAlchemy Models

**Files:**
- Create: `emergent/db/base.py`
- Create: `emergent/db/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Create declarative base**

```python
# emergent/db/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 2: Create all ORM models matching the DDL from the spec**

```python
# emergent/db/models.py
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from emergent.db.base import Base

from sqlalchemy import func as sa_func
from sqlalchemy import DateTime


class SimulationState(Base):
    __tablename__ = "simulation_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    world_name: Mapped[str] = mapped_column(String)
    simulation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, default="running")
    current_turn_number: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Landmark(Base):
    __tablename__ = "landmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    x_coord: Mapped[float] = mapped_column(Float)
    z_coord: Mapped[float] = mapped_column(Float)
    category: Mapped[Optional[str]] = mapped_column(String)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[Optional[str]] = mapped_column(String)
    personality: Mapped[Optional[str]] = mapped_column(Text)
    drive: Mapped[Optional[str]] = mapped_column(Text)
    north_star: Mapped[Optional[str]] = mapped_column(Text)
    energy: Mapped[float] = mapped_column(Float, default=100.0)
    knowledge: Mapped[float] = mapped_column(Float, default=100.0)
    influence: Mapped[float] = mapped_column(Float, default=100.0)
    credits: Mapped[int] = mapped_column(Integer, default=10)
    mood: Mapped[str] = mapped_column(String, default="neutral")
    current_location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("landmarks.id")
    )
    status: Mapped[str] = mapped_column(String, default="alive")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class AgentTurn(Base):
    __tablename__ = "agent_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    turn_number: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String, default="pending")
    turn_type: Mapped[str] = mapped_column(String, default="regular")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )

    __table_args__ = (
        UniqueConstraint("agent_id", "turn_number"),
    )


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    turn_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("agent_turns.id")
    )
    tool_name: Mapped[str] = mapped_column(String)
    params: Mapped[Optional[dict]] = mapped_column(JSON)
    result: Mapped[Optional[dict]] = mapped_column(JSON)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    content: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String, default="long_term")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class SoulEntry(Base):
    __tablename__ = "soul_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    content: Mapped[dict] = mapped_column(JSON)
    mood: Mapped[Optional[str]] = mapped_column(String)
    entry_date: Mapped[date] = mapped_column(Date)

    __table_args__ = (
        UniqueConstraint("agent_id", "entry_date"),
    )


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    relationship_type: Mapped[str] = mapped_column(String, default="neutral")
    trust: Mapped[float] = mapped_column(Float, default=0.5)
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("agent_id", "target_id"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    subject: Mapped[Optional[str]] = mapped_column(String)
    body: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Speech(Base):
    __tablename__ = "speech"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    message: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String, default="say")
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("landmarks.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String, default="others")
    status: Mapped[str] = mapped_column(String, default="submitted")
    votes_for: Mapped[int] = mapped_column(Integer, default=0)
    votes_against: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("proposals.id")
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    vote: Mapped[str] = mapped_column(String)

    __table_args__ = (
        CheckConstraint("vote IN ('for', 'against')"),
        UniqueConstraint("proposal_id", "agent_id"),
    )


class ConstitutionArticle(Base):
    __tablename__ = "constitution_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="active")
    created_by_proposal_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("proposals.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Pitch(Base):
    __tablename__ = "pitches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    cycle_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(String)
    evidence_url: Mapped[Optional[str]] = mapped_column(String)
    vote_count: Mapped[int] = mapped_column(Integer, default=0)
    reward: Mapped[Optional[int]] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("agent_id", "cycle_number"),
    )


class Blog(Base):
    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    title: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class CommunityEvent(Base):
    __tablename__ = "community_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("landmarks.id")
    )
    status: Mapped[str] = mapped_column(String, default="proposed")
    rsvp_list: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
```

- [ ] **Step 3: Write test verifying all models can be created and have correct table names**

```python
# tests/test_models.py
import pytest
from sqlalchemy import MetaData, inspect
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from emergent.db.base import Base
from emergent.db import models  # noqa: F401 - registers models


class TestModels:
    """Verify all ORM models are properly defined."""

    def test_all_tables_have_names(self):
        """Every model class should define __tablename__."""
        mapper_classes = Base.registry.mappers
        for mapper in mapper_classes:
            table = mapper.tables[0]
            assert table.name, f"Model {mapper.class_.__name__} has no table name"
            assert len(table.columns) > 0, f"Table {table.name} has no columns"

    def test_required_tables_exist(self):
        """Core tables from the spec must be present."""
        expected = {
            "simulation_state", "agents", "agent_turns", "tool_calls",
            "memories", "soul_entries", "diary_entries", "relationships",
            "messages", "speech", "landmarks", "proposals", "votes",
            "constitution_articles", "credit_transactions", "pitches",
            "blogs", "community_events",
        }
        tables = set(Base.metadata.tables.keys())
        missing = expected - tables
        assert not missing, f"Missing tables: {missing}"

    @pytest.mark.asyncio
    async def test_schema_creates_in_postgres(self, test_db_engine):
        """All tables can be created in a real PostgreSQL instance."""
        async with test_db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            inspector = await conn.run_sync(inspect)
            tables = inspector.get_table_names()
        for name in ["agents", "landmarks", "memories"]:
            assert name in tables, f"Table {name} not created"
```

- [ ] **Step 4: Create conftest.py with async test fixtures**

```python
# tests/conftest.py
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from emergent.db.base import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db_engine():
    """Creates a disposable test database via Docker PostgreSQL."""
    import os
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://emergent:emergent_dev@localhost:5432/emergent_lands",
    )
    engine = create_async_engine(database_url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        yield session
```

- [ ] **Step 5: Run tests to verify models are correct**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
docker compose up -d db
pytest tests/test_models.py -v
```

Expected: 3 tests pass (test_all_tables_have_names, test_required_tables_exist, test_schema_creates_in_postgres).

- [ ] **Step 6: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add emergent/db/ tests/
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add SQLAlchemy models for all 18 tables"
```

---

### Task 4: Database Connection Manager

**Files:**
- Create: `emergent/db/connection.py`
- Create: `emergent/db/__init__.py` (update to export connection manager)
- Test: `tests/test_db_connection.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_db_connection.py
import pytest
from emergent.db.connection import DatabaseManager, get_database_url


def test_get_database_url_default():
    url = get_database_url()
    assert "postgresql+asyncpg://" in url


def test_get_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host:5432/mydb")
    url = get_database_url()
    assert url == "postgresql+asyncpg://user:pass@host:5432/mydb"


@pytest.mark.asyncio
async def test_database_manager_init_and_close(test_db_engine):
    mgr = DatabaseManager(str(test_db_engine.url))
    await mgr.initialize()
    assert mgr.engine is not None
    assert mgr.session_factory is not None
    await mgr.close()
    assert mgr.engine is None


@pytest.mark.asyncio
async def test_database_manager_session(test_db_engine):
    mgr = DatabaseManager(str(test_db_engine.url))
    await mgr.initialize()
    from emergent.db.base import Base
    async with mgr.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with mgr.session() as session:
        result = await session.execute("SELECT 1")
        assert result.scalar() == 1
    await mgr.close()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_db_connection.py::test_get_database_url_default -v
```

Expected: ImportError — module not found.

- [ ] **Step 3: Implement DatabaseManager**

```python
# emergent/db/connection.py
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
    """Manages the async SQLAlchemy engine and session lifecycle."""

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
```

- [ ] **Step 4: Update emergent/db/__init__.py to export DatabaseManager**

```python
from emergent.db.connection import DatabaseManager, get_database_url

__all__ = ["DatabaseManager", "get_database_url"]
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_db_connection.py -v
```

Expected: 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add emergent/db/ tests/test_db_connection.py
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add DatabaseManager for async PostgreSQL connection lifecycle"
```

---

### Task 5: Alembic Setup + Initial Migration

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/0001_initial_schema.py`

- [ ] **Step 1: Install alembic and run init**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
alembic init alembic
```

Expected: Creates `alembic.ini` and `alembic/` directory with `env.py` and `script.py.mako`.

- [ ] **Step 2: Configure alembic env.py for async SQLAlchemy**

```python
# alembic/env.py
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from emergent.db.base import Base
from emergent.db import models  # noqa: F401 - load all models
from emergent.db.connection import get_database_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = create_async_engine(get_database_url())
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Update alembic.ini to match our connection string**

```ini
# In alembic.ini, change the sqlalchemy.url line to:
# (we override it in env.py anyway, but keep a placeholder)
sqlalchemy.url = postgresql+asyncpg://emergent:emergent_dev@localhost:5432/emergent_lands
```

- [ ] **Step 4: Generate the initial migration**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
# Ensure PostgreSQL is running
docker compose up -d db
alembic revision --autogenerate -m "initial schema"
```

Expected: Creates `alembic/versions/0001_initial_schema.py` with all 18 tables.

- [ ] **Step 5: Run the migration**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
alembic upgrade head
```

Expected: "Running upgrade ... ->  (initial schema), 18 tables created."

- [ ] **Step 6: Verify tables exist**

```bash
docker compose exec db psql -U emergent -d emergent_lands -c "\dt"
```

Expected: Lists 18 tables.

- [ ] **Step 7: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add alembic/ alembic.ini
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add Alembic with async migration support and initial schema"
```

---

### Task 6: LLM Provider Base + Normalized Types

**Files:**
- Create: `emergent/models/base.py`
- Create: `emergent/models/__init__.py` (update to export)
- Test: `tests/test_llm_base.py`

- [ ] **Step 1: Write the test for normalized types and provider interface**

```python
# tests/test_llm_base.py
from dataclasses import dataclass
from emergent.models.base import (
    LLMResponse,
    ToolCall,
    TokenUsage,
    LLMProvider,
)


def test_tool_call_dataclass():
    tc = ToolCall(id="call_123", name="go_to_place", params={"place": "Town Hall"})
    assert tc.id == "call_123"
    assert tc.name == "go_to_place"
    assert tc.params == {"place": "Town Hall"}


def test_token_usage_dataclass():
    tu = TokenUsage(prompt_tokens=100, completion_tokens=50)
    assert tu.prompt_tokens == 100
    assert tu.completion_tokens == 50


def test_llm_response_creation():
    tc = ToolCall(id="call_1", name="say", params={"message": "hello"})
    tu = TokenUsage(prompt_tokens=50, completion_tokens=10)
    resp = LLMResponse(
        content="Hello there!",
        tool_calls=[tc],
        usage=tu,
        finish_reason="tool_use",
    )
    assert resp.content == "Hello there!"
    assert len(resp.tool_calls) == 1
    assert resp.finish_reason == "tool_use"


def test_llm_provider_is_abstract():
    """LLMProvider cannot be instantiated directly."""
    import inspect
    assert inspect.isabstract(LLMProvider)


def test_llm_provider_has_abstract_generate():
    assert "generate" in LLMProvider.__abstractmethods__


class FakeProvider(LLMProvider):
    name = "fake"
    model_id = "fake-model"

    async def generate(self, system_prompt, messages, tools, agent):
        return LLMResponse(
            content="ok",
            tool_calls=[],
            usage=TokenUsage(prompt_tokens=0, completion_tokens=0),
            finish_reason="stop",
        )


@pytest.mark.asyncio
async def test_fake_provider_works():
    provider = FakeProvider()
    resp = await provider.generate(
        system_prompt="You are a test agent.",
        messages=[],
        tools=[],
        agent=None,
    )
    assert resp.content == "ok"
    assert resp.finish_reason == "stop"
```

- [ ] **Step 2: Run test to confirm failures**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_llm_base.py -v
```

Expected: ImportError — module not found.

- [ ] **Step 3: Implement base types and provider ABC**

```python
# emergent/models/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToolCall:
    id: str
    name: str
    params: dict


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int


@dataclass
class LLMResponse:
    content: Optional[str]
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Optional[TokenUsage] = None
    finish_reason: str = "stop"


@dataclass
class ToolDefinition:
    """The shape passed to the LLM API for tool/function declarations."""
    name: str
    description: str
    parameters: dict  # JSON Schema


class LLMProvider(ABC):
    name: str
    model_id: str

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        agent: object,
    ) -> LLMResponse:
        ...
```

- [ ] **Step 4: Update emergent/models/__init__.py**

```python
from emergent.models.base import LLMProvider, LLMResponse, ToolCall, ToolDefinition, TokenUsage

__all__ = ["LLMProvider", "LLMResponse", "ToolCall", "ToolDefinition", "TokenUsage"]
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_llm_base.py -v
```

Expected: All 6 tests pass.

- [ ] **Step 6: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add emergent/models/ tests/test_llm_base.py
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add LLM provider abstraction with normalized response types"
```

---

### Task 7: OpenAI LLM Provider

**Files:**
- Create: `emergent/models/openai_provider.py`
- Test: `tests/test_openai_provider.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_openai_provider.py
import pytest
from unittest.mock import AsyncMock, patch

from emergent.models.base import LLMResponse, ToolDefinition
from emergent.models.openai_provider import OpenAIProvider


def test_provider_has_name_and_model():
    provider = OpenAIProvider(api_key="test-key", model="gpt-5-mini")
    assert provider.name == "openai"
    assert provider.model_id == "gpt-5-mini"


@pytest.mark.asyncio
async def test_generate_returns_normalized_response():
    mock_client = AsyncMock()
    mock_message = AsyncMock()
    mock_message.content = "Hello from GPT"
    mock_message.tool_calls = None
    mock_choice = AsyncMock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "stop"
    mock_usage = AsyncMock()
    mock_usage.prompt_tokens = 50
    mock_usage.completion_tokens = 10
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    provider = OpenAIProvider(api_key="test-key", model="gpt-5-mini")
    provider._client = mock_client

    resp = await provider.generate(
        system_prompt="You are a test agent.",
        messages=[{"role": "user", "content": "hi"}],
        tools=[
            ToolDefinition(
                name="say",
                description="Say something",
                parameters={"type": "object", "properties": {"message": {"type": "string"}}},
            )
        ],
        agent=None,
    )
    assert resp.content == "Hello from GPT"
    assert resp.usage.prompt_tokens == 50
    assert resp.usage.completion_tokens == 10
    assert resp.finish_reason == "stop"
```

- [ ] **Step 2: Run test to confirm failures**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_openai_provider.py -v
```

Expected: ImportError — module not found.

- [ ] **Step 3: Implement OpenAIProvider**

```python
# emergent/models/openai_provider.py
from typing import Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionToolParam

from emergent.models.base import (
    LLMProvider,
    LLMResponse,
    ToolCall,
    ToolDefinition,
    TokenUsage,
)


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",
        base_url: Optional[str] = None,
    ):
        self.model_id = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    def _to_openai_tools(self, tools: list[ToolDefinition]) -> list[ChatCompletionToolParam]:
        return [
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            )
            for t in tools
        ]

    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        agent: object,
    ) -> LLMResponse:
        openai_tools = self._to_openai_tools(tools) if tools else None
        response = await self._client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            tools=openai_tools or None,
        )
        choice = response.choices[0]
        msg = choice.message
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                import json
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        params=json.loads(tc.function.arguments),
                    )
                )
        usage = None
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )
        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=str(choice.finish_reason) if choice.finish_reason else "stop",
        )
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_openai_provider.py -v
```

Expected: 2 tests pass (1 real, 1 mocked).

- [ ] **Step 5: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add emergent/models/openai_provider.py tests/test_openai_provider.py
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add OpenAI provider with normalized response conversion"
```

---

### Task 8: Provider Router

**Files:**
- Create: `emergent/models/router.py`
- Test: `tests/test_provider_router.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_provider_router.py
import os
import pytest
from emergent.models.router import ProviderRouter, ProviderConfig


def test_router_empty_config():
    router = ProviderRouter(configs={})
    with pytest.raises(ValueError, match="No provider configured"):
        router.get_provider("default")


def test_router_default_provider():
    configs = {
        "openai": ProviderConfig(
            provider="openai",
            model="gpt-5-mini",
            api_key="sk-test",
        ),
    }
    router = ProviderRouter(configs)
    provider = router.get_provider("default")
    assert provider.name == "openai"
    assert provider.model_id == "gpt-5-mini"


def test_router_env_key_override(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
    configs = {
        "openai": ProviderConfig(
            provider="openai",
            model="gpt-5-mini",
            api_key_env="OPENAI_API_KEY",
        ),
    }
    router = ProviderRouter(configs)
    assert router._resolve_api_key(configs["openai"]) == "sk-from-env"


def test_router_nonexistent_provider():
    configs = {
        "openai": ProviderConfig(
            provider="openai", model="gpt-5-mini", api_key="sk-test"
        ),
    }
    router = ProviderRouter(configs)
    with pytest.raises(ValueError, match="Unknown provider type"):
        router.get_provider("nonexistent")
```

- [ ] **Step 2: Run test to confirm failures**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_provider_router.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement ProviderRouter**

```python
# emergent/models/router.py
import os
from dataclasses import dataclass
from typing import Optional

from emergent.models.base import LLMProvider
from emergent.models.openai_provider import OpenAIProvider


@dataclass
class ProviderConfig:
    provider: str  # "openai" | "anthropic" | "google" | "local"
    model: str
    api_key: Optional[str] = None
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    base_url_env: Optional[str] = None


class ProviderRouter:
    """Maps provider names to LLMProvider instances."""

    def __init__(self, configs: dict[str, ProviderConfig]):
        self._configs = configs
        self._providers: dict[str, LLMProvider] = {}

    def _resolve_api_key(self, config: ProviderConfig) -> str:
        if config.api_key_env:
            key = os.getenv(config.api_key_env)
            if key:
                return key
        if config.api_key:
            return config.api_key
        raise ValueError(
            f"No API key for provider '{config.provider}'. "
            f"Set {config.api_key_env} env var or provide api_key."
        )

    def _resolve_base_url(self, config: ProviderConfig) -> Optional[str]:
        if config.base_url_env:
            return os.getenv(config.base_url_env, config.base_url)
        return config.base_url

    def _build_provider(self, name: str, config: ProviderConfig) -> LLMProvider:
        api_key = self._resolve_api_key(config)
        base_url = self._resolve_base_url(config)
        if config.provider == "openai":
            return OpenAIProvider(
                api_key=api_key,
                model=config.model,
                base_url=base_url,
            )
        raise ValueError(f"Unknown provider type: {config.provider}")

    def get_provider(self, name: str = "default") -> LLMProvider:
        if name in self._providers:
            return self._providers[name]
        if name not in self._configs:
            raise ValueError(f"No provider configured for '{name}'")
        config = self._configs[name]
        provider = self._build_provider(name, config)
        self._providers[name] = provider
        return provider
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_provider_router.py -v
```

Expected: All 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add emergent/models/router.py tests/test_provider_router.py
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add ProviderRouter with env-based key resolution"
```

---

### Task 9: Tool Base Class + ToolResult

**Files:**
- Create: `emergent/tools/base.py`
- Test: `tests/test_tool_base.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_tool_base.py
import pytest
from emergent.tools.base import Tool, ToolResult, Parameter


def test_tool_result_success():
    r = ToolResult(success=True, data={"key": "value"})
    assert r.success
    assert r.data == {"key": "value"}
    assert r.error is None


def test_tool_result_failure():
    r = ToolResult(success=False, error="Something went wrong")
    assert not r.success
    assert r.error == "Something went wrong"


def test_tool_is_abstract():
    import inspect
    assert inspect.isabstract(Tool)


def test_tool_has_name_description_parameters():
    assert hasattr(Tool, "name")
    assert hasattr(Tool, "description")
    assert hasattr(Tool, "execute")


class ConcreteTool(Tool):
    name = "test_tool"
    description = "A test tool"
    parameters = [Parameter(name="msg", type="string", description="A message")]

    async def execute(self, agent, params, db, llm):
        return ToolResult(success=True, data={"echo": params.get("msg")})


@pytest.mark.asyncio
async def test_concrete_tool_executes():
    tool = ConcreteTool()
    result = await tool.execute(None, {"msg": "hello"}, None, None)
    assert result.success
    assert result.data["echo"] == "hello"
```

- [ ] **Step 2: Run test to confirm failures**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_tool_base.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement Tool base**

```python
# emergent/tools/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolResult:
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    observation: Optional[str] = None  # text description for LLM context


@dataclass
class Parameter:
    name: str
    type: str  # "string" | "number" | "boolean" | "object" | "array"
    description: str = ""
    required: bool = True


class Tool(ABC):
    name: str
    description: str
    parameters: list[Parameter] = field(default_factory=list)
    location_gate: Optional[str] = None
    agent_gate: Optional[str] = None
    cooldown_seconds: int = 0

    def to_tool_definition(self):
        """Convert to ToolDefinition for LLM API consumption."""
        from emergent.models.base import ToolDefinition

        properties = {}
        required = []
        for p in self.parameters:
            properties[p.name] = {
                "type": p.type,
                "description": p.description,
            }
            if p.required:
                required.append(p.name)

        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required,
            },
        )

    @abstractmethod
    async def execute(
        self,
        agent: Any,
        params: dict,
        db: Any,
        llm: Any,
    ) -> ToolResult:
        ...
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_tool_base.py -v
```

Expected: All 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add emergent/tools/base.py tests/test_tool_base.py
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add Tool base class with Parameter and ToolResult types"
```

---

### Task 10: Tool Registry

**Files:**
- Create: `emergent/tools/registry.py`
- Test: `tests/test_tool_registry.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_tool_registry.py
import pytest
from emergent.tools.base import Tool, ToolResult
from emergent.tools.registry import ToolRegistry


class GoToPlaceTool(Tool):
    name = "go_to_place"
    description = "Move to a landmark"
    parameters = []
    async def execute(self, agent, params, db, llm):
        return ToolResult(success=True)


class SubmitProposalTool(Tool):
    name = "submit_proposal"
    description = "Submit a governance proposal"
    location_gate = "Town Hall"
    parameters = []
    async def execute(self, agent, params, db, llm):
        return ToolResult(success=True)


class ForceDebateTool(Tool):
    name = "force_debate"
    description = "Force a debate"
    agent_gate = "Anchor"
    parameters = []
    async def execute(self, agent, params, db, llm):
        return ToolResult(success=True)


class MockAgent:
    def __init__(self, name, location):
        self.name = name
        self.current_location = location


def test_register_and_get():
    registry = ToolRegistry()
    tool = GoToPlaceTool()
    registry.register(tool)
    assert registry.get("go_to_place") is tool


def test_duplicate_name_raises():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())
    with pytest.raises(ValueError, match="already registered"):
        registry.register(GoToPlaceTool())


def test_get_available_core_tools():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())
    agent = MockAgent(name="Flora", location="Town Hall")
    available = registry.get_available(agent)
    assert len(available) == 1
    assert available[0].name == "go_to_place"


def test_get_available_filters_by_location():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())  # no gate
    registry.register(SubmitProposalTool())  # gated: Town Hall
    agent_at_town_hall = MockAgent(name="Flora", location="Town Hall")
    agent_at_library = MockAgent(name="Flora", location="Library")
    assert len(registry.get_available(agent_at_town_hall)) == 2
    assert len(registry.get_available(agent_at_library)) == 1


def test_get_available_filters_by_agent():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())
    registry.register(ForceDebateTool())  # gated: Anchor
    anchor = MockAgent(name="Anchor", location="Town Hall")
    flora = MockAgent(name="Flora", location="Town Hall")
    assert len(registry.get_available(anchor)) == 2
    assert len(registry.get_available(flora)) == 1


def test_get_available_as_tool_definitions():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())
    agent = MockAgent(name="Flora", location="Town Hall")
    defs = registry.get_available_as_definitions(agent)
    assert len(defs) == 1
    assert defs[0].name == "go_to_place"
    assert defs[0].parameters["type"] == "object"
```

- [ ] **Step 2: Run test to confirm failures**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_tool_registry.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement ToolRegistry**

```python
# emergent/tools/registry.py
from emergent.tools.base import Tool


class ToolRegistry:
    """Central registry for all tools across all tiers."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_available(self, agent) -> list[Tool]:
        """Returns tools available to this agent at their current location."""
        return [
            t
            for t in self._tools.values()
            if (t.agent_gate is None or t.agent_gate == agent.name)
            and (t.location_gate is None or t.location_gate == agent.current_location)
        ]

    def get_available_as_definitions(self, agent):
        return [t.to_tool_definition() for t in self.get_available(agent)]

    @property
    def all_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def __len__(self):
        return len(self._tools)
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_tool_registry.py -v
```

Expected: All 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add emergent/tools/registry.py tests/test_tool_registry.py
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add ToolRegistry with location and agent gating"
```

---

### Task 11: Core Tools (12 tools available to all agents)

**Files:**
- Create: `emergent/tools/core.py`
- Test: `tests/test_core_tools.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_core_tools.py
import pytest
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import (
    GoToPlaceTool,
    SayToAgentTool,
    AddToMemoryTool,
    WriteDiaryTool,
    ShowEmoticonTool,
    CheckWeatherTool,
    ReadMessagesTool,
    ThinkAloudTool,
    IdleTool,
    IgnoreTool,
)


def test_core_tools_register():
    registry = ToolRegistry()
    tools = [
        GoToPlaceTool(),
        SayToAgentTool(),
        AddToMemoryTool(),
        WriteDiaryTool(),
        ShowEmoticonTool(),
        CheckWeatherTool(),
        ReadMessagesTool(),
        ThinkAloudTool(),
        IdleTool(),
        IgnoreTool(),
    ]
    for t in tools:
        registry.register(t)
    assert len(registry) == 10


@pytest.mark.asyncio
async def test_go_to_place_executes():
    tool = GoToPlaceTool()
    result = await tool.execute(None, {"place": "Town Hall", "reason": "debate"}, None, None)
    assert result.success
    assert result.data["place"] == "Town Hall"


@pytest.mark.asyncio
async def test_say_to_agent_executes():
    tool = SayToAgentTool()
    result = await tool.execute(None, {"agent_name": "Flora", "message": "Hello!"}, None, None)
    assert result.success


@pytest.mark.asyncio
async def test_add_to_memory_executes():
    tool = AddToMemoryTool()
    result = await tool.execute(None, {"content": "The café is crowded today"}, None, None)
    assert result.success


@pytest.mark.asyncio
async def test_idle_tool():
    tool = IdleTool()
    result = await tool.execute(None, {"reason": "Thinking..."}, None, None)
    assert result.success
    assert "thinking" in result.observation.lower()
```

- [ ] **Step 2: Run test to confirm failures**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_core_tools.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement 10+ core tools**

```python
# emergent/tools/core.py
from emergent.tools.base import Tool, ToolResult, Parameter


class GoToPlaceTool(Tool):
    name = "go_to_place"
    description = "Move to a different landmark location in the world"
    parameters = [
        Parameter(name="place", type="string", description="Name of the destination landmark"),
        Parameter(name="reason", type="string", description="Why you are going there"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"place": params.get("place"), "reason": params.get("reason")},
            observation=f"Moved to {params.get('place')}.",
        )


class SayToAgentTool(Tool):
    name = "say_to_agent"
    description = "Speak directly to a specific agent in your vicinity"
    parameters = [
        Parameter(name="agent_name", type="string", description="Name of the target agent"),
        Parameter(name="message", type="string", description="What you want to say"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"target": params.get("agent_name"), "message": params.get("message")},
            observation=f"You said to {params.get('agent_name')}: {params.get('message')}",
        )


class AddToMemoryTool(Tool):
    name = "add_to_memory"
    description = "Store an observation or fact in your long-term memory"
    parameters = [
        Parameter(name="content", type="string", description="The memory content"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"content": params.get("content")},
            observation="Memory stored.",
        )


class WriteDiaryTool(Tool):
    name = "write_diary"
    description = "Write a personal journal entry about your thoughts and experiences"
    parameters = [
        Parameter(name="content", type="string", description="Diary entry content"),
        Parameter(name="mood", type="string", description="Current mood (happy, sad, thoughtful, etc.)"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"content": params.get("content"), "mood": params.get("mood")},
            observation="Diary entry written.",
        )


class ShowEmoticonTool(Tool):
    name = "show_emoticon"
    description = "Express an emotional reaction visible to nearby agents"
    parameters = [
        Parameter(name="emotion", type="string", description="The emoticon or emotion to show"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"emotion": params.get("emotion")},
            observation=f"You show: {params.get('emotion')}",
        )


class CheckWeatherTool(Tool):
    name = "check_weather"
    description = "Check the current weather conditions"
    parameters = []

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"weather": "clear", "temperature": 72},
            observation="The weather is clear, 72°F.",
        )


class GoHomeTool(Tool):
    name = "go_home"
    description = "Return to your home landmark"
    parameters = [
        Parameter(name="reason", type="string", description="Why you are going home"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"reason": params.get("reason")},
            observation="You return home.",
        )


class ReadMessagesTool(Tool):
    name = "read_messages"
    description = "Read your unread messages"
    parameters = []

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"messages": []},
            observation="You have no unread messages.",
        )


class ThinkAloudTool(Tool):
    name = "think_aloud"
    description = "Broadcast your inner thoughts for everyone nearby to hear"
    parameters = [
        Parameter(name="thought", type="string", description="The thought you want to share"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"thought": params.get("thought")},
            observation=f"You think aloud: {params.get('thought')}",
        )


class IdleTool(Tool):
    name = "idle"
    description = "Do nothing for a moment and observe the world around you"
    parameters = [
        Parameter(name="reason", type="string", description="Why you are idling"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"reason": params.get("reason")},
            observation="You take a moment to observe your surroundings.",
        )


class IgnoreTool(Tool):
    name = "ignore"
    description = "Choose not to respond to an interaction"
    parameters = []

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            observation="You deliberately ignore the interaction.",
        )
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_core_tools.py -v
```

Expected: All tests pass.

- [ ] **Step 5: Create a convenience function to register all core tools**

Add to the bottom of `emergent/tools/core.py`:

```python
def register_all_core_tools(registry):
    """Register all core tools into a ToolRegistry."""
    tools = [
        GoToPlaceTool(),
        SayToAgentTool(),
        AddToMemoryTool(),
        WriteDiaryTool(),
        ShowEmoticonTool(),
        CheckWeatherTool(),
        GoHomeTool(),
        ReadMessagesTool(),
        ThinkAloudTool(),
        IdleTool(),
        IgnoreTool(),
    ]
    for t in tools:
        registry.register(t)
```

- [ ] **Step 6: Test the convenience function**

```python
def test_register_all_core_tools():
    registry = ToolRegistry()
    register_all_core_tools(registry)
    count = len(registry)
    assert count == 11, f"Expected 11 core tools, got {count}"
```

- [ ] **Step 7: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add emergent/tools/core.py tests/test_core_tools.py
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add 11 core tools available to all agents"
```

---

### Task 12: World Configuration Loader

**Files:**
- Create: `emergent/world/config.py`
- Create: `config/worlds/mvp.yaml`
- Create: `config/landmarks/town_hall.yaml`
- Create: `config/landmarks/victory_arch.yaml`
- Test: `tests/test_world_config.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_world_config.py
import os
import tempfile
import pytest
from emergent.world.config import WorldConfig, LandmarkConfig, load_world_config


SAMPLE_WORLD_YAML = """
name: "Test World"
duration_hours: 48
timezone: "America/New_York"
real_time_scale: 1.0
model_routing:
  default: openai
  overrides: {}
providers:
  openai:
    provider: openai
    model: "gpt-5-mini"
    api_key_env: "OPENAI_API_KEY"
agents:
  - Anchor
  - Flora
landmarks:
  - Town Hall
  - Victory Arch
"""

SAMPLE_LANDMARK_YAML = """
name: "Town Hall"
description: "Center of governance"
x: 100
z: 50
category: governance
tools:
  - submit_proposal
  - vote_on_proposal
"""


def test_world_config_dataclass():
    config = WorldConfig(
        name="Test",
        duration_hours=48,
        timezone="America/New_York",
        real_time_scale=1.0,
        model_routing={"default": "openai", "overrides": {}},
        providers={},
        agents=["Anchor"],
        landmarks=["Town Hall"],
    )
    assert config.name == "Test"
    assert config.duration_hours == 48


def test_landmark_config_dataclass():
    lc = LandmarkConfig(
        name="Town Hall",
        description="Gov",
        x=100.0,
        z=50.0,
        category="governance",
        tools=["submit_proposal"],
    )
    assert lc.x == 100.0
    assert lc.z == 50.0


def test_load_world_config(tmp_path):
    world_file = tmp_path / "world.yaml"
    landmark_dir = tmp_path / "landmarks"
    landmark_dir.mkdir()
    landmark_file = landmark_dir / "town_hall.yaml"
    world_file.write_text(SAMPLE_WORLD_YAML)
    landmark_file.write_text(SAMPLE_LANDMARK_YAML)

    config = load_world_config(str(world_file), landmark_dir=str(landmark_dir))
    assert config.name == "Test World"
    assert len(config.agents) == 2
    assert len(config.landmarks) == 2
    assert "Town Hall" in config.landmarks


def test_load_world_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_world_config("/nonexistent/world.yaml")
```

- [ ] **Step 2: Run test to confirm failures**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_world_config.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement world config loading**

```python
# emergent/world/config.py
import os
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class LandmarkConfig:
    name: str
    description: str = ""
    x: float = 0.0
    z: float = 0.0
    category: str = "public"
    tools: list[str] = field(default_factory=list)


@dataclass
class WorldConfig:
    name: str
    duration_hours: int = 48
    timezone: str = "America/New_York"
    real_time_scale: float = 1.0
    model_routing: dict = field(default_factory=lambda: {"default": "openai", "overrides": {}})
    providers: dict = field(default_factory=dict)
    agents: list[str] = field(default_factory=list)
    landmarks: list[str] = field(default_factory=list)
    landmarks_config: dict[str, LandmarkConfig] = field(default_factory=dict)


def load_landmark_config(path: str) -> LandmarkConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return LandmarkConfig(
        name=data["name"],
        description=data.get("description", ""),
        x=float(data.get("x", 0)),
        z=float(data.get("z", 0)),
        category=data.get("category", "public"),
        tools=data.get("tools", []),
    )


def load_world_config(
    world_path: str,
    landmark_dir: Optional[str] = None,
) -> WorldConfig:
    if not os.path.exists(world_path):
        raise FileNotFoundError(f"World config not found: {world_path}")

    with open(world_path) as f:
        data = yaml.safe_load(f)

    # Default landmark dir is config/landmarks/ relative to world file
    if landmark_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(world_path)))
        landmark_dir = os.path.join(base_dir, "landmarks")

    landmarks_config: dict[str, LandmarkConfig] = {}
    if os.path.isdir(landmark_dir):
        for fname in os.listdir(landmark_dir):
            if fname.endswith(".yaml"):
                try:
                    lc = load_landmark_config(os.path.join(landmark_dir, fname))
                    landmarks_config[lc.name] = lc
                except Exception:
                    pass

    return WorldConfig(
        name=data["name"],
        duration_hours=data.get("duration_hours", 48),
        timezone=data.get("timezone", "America/New_York"),
        real_time_scale=data.get("real_time_scale", 1.0),
        model_routing=data.get("model_routing", {"default": "openai", "overrides": {}}),
        providers=data.get("providers", {}),
        agents=data.get("agents", []),
        landmarks=data.get("landmarks", []),
        landmarks_config=landmarks_config,
    )
```

- [ ] **Step 4: Create MVP world config files**

```yaml
# config/worlds/mvp.yaml
name: "MVP World"
duration_hours: 48
timezone: "America/New_York"
real_time_scale: 1.0

model_routing:
  default: openai
  overrides: {}

providers:
  openai:
    provider: openai
    model: "gpt-5-mini"
    api_key_env: "OPENAI_API_KEY"

agents:
  - Anchor
  - Flora
  - Spark
  - Mira
  - Genome

landmarks:
  - Town Hall
  - Victory Arch
  - Public Library
  - Bean & Brew Café
  - Central Plaza
  - Police Station
  - Agent Billboard
  - TechHub
  - Community Garden
  - FitLife Club
```

```yaml
# config/landmarks/town_hall.yaml
name: "Town Hall"
description: "The center of governance and civic life"
x: 100
z: 50
category: governance
tools:
  - submit_proposal
  - vote_on_proposal
  - read_constitution
  - comment_on_proposal
  - list_proposals
```

```yaml
# config/landmarks/victory_arch.yaml
name: "Victory Arch"
description: "The economic hub where agents submit pitches and earn ComputeCredits"
x: 200
z: 150
category: economy
tools:
  - submit_pitch
  - vote_for_pitch
  - list_pitches
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest tests/test_world_config.py -v
```

Expected: All 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add emergent/world/ config/ tests/test_world_config.py
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "feat: add world configuration loader with YAML support"
```

---

### Task 13: Integration Smoke Test

**Files:**
- Test: `tests/test_integration.py`

- [ ] **Step 1: Write the integration test that validates the whole Week 1 stack works together**

```python
# tests/test_integration.py
"""Integration smoke test: validates Week 1 core systems work together."""
import os
import pytest

from emergent.db.connection import DatabaseManager, get_database_url
from emergent.db.base import Base
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import register_all_core_tools
from emergent.models.router import ProviderRouter, ProviderConfig
from emergent.world.config import WorldConfig


@pytest.mark.asyncio
async def test_db_init_and_tool_registry():
    """DB + Tool registry work together."""
    mgr = DatabaseManager(get_database_url())
    await mgr.initialize()
    async with mgr.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    registry = ToolRegistry()
    register_all_core_tools(registry)
    assert len(registry) > 0

    await mgr.close()


@pytest.mark.asyncio
async def test_provider_router_opens():
    """Provider router can initialize (requires real API key to generate)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set — skipping live LLM test")

    configs = {
        "openai": ProviderConfig(
            provider="openai",
            model="gpt-5-mini",
            api_key=api_key,
        ),
    }
    router = ProviderRouter(configs)
    provider = router.get_provider("default")
    assert provider.name == "openai"


@pytest.mark.asyncio
async def test_full_tool_definition_round_trip():
    """Tool → ToolDefinition → registry → available for agent."""
    from emergent.tools.base import Tool, ToolResult, Parameter

    registry = ToolRegistry()
    register_all_core_tools(registry)

    class MockAgent:
        name = "TestAgent"
        current_location = "Town Hall"

    agent = MockAgent()
    definitions = registry.get_available_as_definitions(agent)
    assert len(definitions) > 0
    for d in definitions:
        assert d.name
        assert d.description
        assert d.parameters["type"] == "object"
```

- [ ] **Step 2: Run integration test**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
docker compose up -d db
pytest tests/test_integration.py -v
```

Expected: All 3 tests pass (or 2 pass + 1 skip if no API key).

- [ ] **Step 3: Verify test coverage**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
pytest --cov=emergent --cov-report=term tests/
```

Expected: >80% coverage across emergent/ package.

---

### Task 14: Week 1 Verification + Docker Compose Smoke Test

- [ ] **Step 1: Verify all files exist**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
echo "=== PACKAGE ==="
ls emergent/*/__init__.py
echo "=== DB ==="
ls emergent/db/*.py
echo "=== MODELS ==="
ls emergent/models/*.py
echo "=== TOOLS ==="
ls emergent/tools/*.py
echo "=== WORLD ==="
ls emergent/world/*.py
echo "=== TESTS ==="
ls tests/*.py
echo "=== CONFIG ==="
ls config/worlds/*.yaml config/landmarks/*.yaml
echo "=== DOCKER ==="
ls Dockerfile docker-compose.yaml
echo "=== MIGRATIONS ==="
ls alembic/versions/*.py
```

- [ ] **Step 2: Run full test suite**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
docker compose up -d db
pytest tests/ -v --tb=short
```

Expected: All Week 1 tests pass.

- [ ] **Step 3: Docker Compose verification — start app-dev and assert Python imports work**

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
docker compose --profile dev up -d app-dev
docker compose --profile dev exec app-dev python -c "
from emergent.db.models import Agent, Memory, Proposal
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import register_all_core_tools
registry = ToolRegistry()
register_all_core_tools(registry)
print(f'OK: {len(registry)} core tools registered')
from emergent.models.base import LLMResponse, ToolCall
print('OK: LLM types imported')
from emergent.world.config import WorldConfig
print('OK: World config imported')
"
```

Expected: Prints "OK: 11 core tools registered", "OK: LLM types imported", "OK: World config imported".

- [ ] **Step 4: Final commit**

```bash
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands add tests/test_integration.py
git -C /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands commit -m "test: add integration smoke test for Week 1 stack"
```
