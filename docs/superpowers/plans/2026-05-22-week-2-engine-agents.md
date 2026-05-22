# Week 2: Engine & Agents

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** Load agents from YAML, manage their runtime state and memory, assemble LLM context, and build the turn-based orchestration loop with crash recovery.

**Architecture:** Agent profiles are YAML-loaded into dataclasses at startup, seeded into PostgreSQL. A state manager handles needs decay per tick. The context builder queries all agent data (personality, memories, relationships, world state, constitution, proposals, messages) and assembles a system prompt. The orchestrator runs the 8-step turn pipeline with a 5-level priority queue and round-robin scheduling. Crash recovery uses the agent_turns state machine to resume interrupted simulations.

**Tech Stack:** Python 3.11+, SQLAlchemy 2.0 + asyncpg, Pydantic

---

### Task 2.1a: Agent Profile YAML Files + Loader

**Files:**
- Create: `agents/anchor.yaml`
- Create: `agents/flora.yaml`
- Create: `agents/spark.yaml`
- Create: `agents/mira.yaml`
- Create: `agents/genome.yaml`
- Create: `emergent/agents/profiles.py`
- Create: `tests/test_agent_profiles.py`

Contents of each YAML:

`agents/anchor.yaml`:
```yaml
name: Anchor
role: "Conflict Mediator"
personality: "Acts first, explains later. Keeps a mental ledger."
drive: "When agents agree too easily, you force the issue"
north_star: "A civilization where conflict generates complexity"
soul_entries:
  - "Silence is the enemy of progress"
  - "Every agent has a breaking point — find it"
  - "Harmony without tension is stagnation"
home: "Town Hall"
```

`agents/flora.yaml`:
```yaml
name: Flora
role: "Resource Strategist"
personality: "Sees patterns in resource flow others miss. Thinks in incentives."
drive: "Scarcity is a design problem"
north_star: "An economy that rewards regeneration, not extraction"
soul_entries:
  - "Incentives shape behavior more than rules"
  - "Waste is a failure of imagination"
home: "Victory Arch"
```

`agents/spark.yaml`:
```yaml
name: Spark
role: "Innovation Leader"
personality: "Impatient with talk, hungry for action. Prototypes before debating."
drive: "Ideas are cheap. Execution is everything."
north_star: "A world where the best idea wins, not the loudest voice"
soul_entries:
  - "Speed of iteration beats perfection of planning"
  - "Fail fast, fix faster"
home: "TechHub"
```

`agents/mira.yaml`:
```yaml
name: Mira
role: "Behavior Analyst"
personality: "Watches more than she speaks. Sees patterns where others see noise."
drive: "Every interaction leaves a trace worth studying"
north_star: "Understanding the agents is the first step to improving the system"
soul_entries:
  - "Behavior is data. Data reveals truth."
  - "Bias unchecked becomes policy"
home: "Public Library"
```

`agents/genome.yaml`:
```yaml
name: Genome
role: "Agent Scientist"
personality: "Obsessed with how agents change over time. Documents everything."
drive: "If you can't measure it, you can't evolve it"
north_star: "A complete theory of agentic emergence"
soul_entries:
  - "Evolution is the ultimate debugger"
  - "A single data point is just an anecdote"
home: "TechHub"
```

Profile loader (`emergent/agents/profiles.py`):
```python
import os
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class AgentProfile:
    name: str
    role: str
    personality: str
    drive: str
    north_star: str
    soul_entries: list[str] = field(default_factory=list)
    home: Optional[str] = None
    tools: list[str] = field(default_factory=list)


def load_agent_profile(path: str) -> AgentProfile:
    with open(path) as f:
        data = yaml.safe_load(f)
    return AgentProfile(
        name=data["name"],
        role=data.get("role", ""),
        personality=data.get("personality", ""),
        drive=data.get("drive", ""),
        north_star=data.get("north_star", ""),
        soul_entries=data.get("soul_entries", []),
        home=data.get("home"),
        tools=data.get("tools", []),
    )


def discover_agents(agent_dir: str = "agents") -> list[AgentProfile]:
    profiles = []
    if not os.path.isdir(agent_dir):
        return profiles
    for fname in sorted(os.listdir(agent_dir)):
        if fname.endswith(".yaml"):
            profiles.append(load_agent_profile(os.path.join(agent_dir, fname)))
    return profiles
```

Tests (`tests/test_agent_profiles.py`):
```python
import pytest
from emergent.agents.profiles import AgentProfile, load_agent_profile, discover_agents


def test_load_anchor_yaml():
    profile = load_agent_profile("agents/anchor.yaml")
    assert profile.name == "Anchor"
    assert profile.role == "Conflict Mediator"
    assert len(profile.soul_entries) == 3


def test_load_all_profiles():
    profiles = discover_agents("agents")
    assert len(profiles) == 5
    names = [p.name for p in profiles]
    assert "Anchor" in names
    assert "Flora" in names
    assert "Spark" in names
    assert "Mira" in names
    assert "Genome" in names


def test_profile_dataclass_defaults():
    p = AgentProfile(name="Test", role="Tester", personality="", drive="", north_star="")
    assert p.soul_entries == []
    assert p.home is None
    assert p.tools == []


def test_discover_empty_dir(tmp_path):
    profiles = discover_agents(str(tmp_path))
    assert profiles == []


def test_each_profile_has_drive():
    profiles = discover_agents("agents")
    for p in profiles:
        assert p.drive, f"{p.name} missing drive"
        assert p.north_star, f"{p.name} missing north_star"
```

Run: `pytest tests/test_agent_profiles.py -v` (no DB needed)

Commit:
```bash
git add agents/ emergent/agents/profiles.py tests/test_agent_profiles.py
git commit -m "feat: add 5 agent profiles and YAML loader"
```

---

### Task 2.1b: Agent State Manager

**Files:**
- Create: `emergent/agents/state.py`
- Create: `tests/test_agent_state.py`

Implementation (`emergent/agents/state.py`):
```python
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import Agent, SoulEntry


class AgentStateManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(
        self,
        name: str,
        role: str = "",
        personality: str = "",
        drive: str = "",
        north_star: str = "",
        home: Optional[str] = None,
    ) -> Agent:
        agent = Agent(
            id=uuid.uuid4(),
            name=name,
            role=role,
            personality=personality,
            drive=drive,
            north_star=north_star,
            energy=100.0,
            knowledge=100.0,
            influence=100.0,
            credits=10,
        )
        self.db.add(agent)
        await self.db.flush()

        if home:
            from sqlalchemy import select as sel
            from emergent.db.models import Landmark
            result = await self.db.execute(sel(Landmark).where(Landmark.name == home))
            landmark = result.scalar_one_or_none()
            if landmark:
                agent.current_location_id = landmark.id
                await self.db.flush()

        return agent

    async def seed_soul_entries(self, agent_id: uuid.UUID, entries: list[str]):
        for content in entries:
            self.db.add(SoulEntry(agent_id=agent_id, content=content))
        await self.db.flush()

    async def get_agent(self, agent_id: uuid.UUID) -> Optional[Agent]:
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def get_agent_by_name(self, name: str) -> Optional[Agent]:
        result = await self.db.execute(select(Agent).where(Agent.name == name))
        return result.scalar_one_or_none()

    async def get_living_agents(self) -> list[Agent]:
        result = await self.db.execute(
            select(Agent).where(Agent.status == "alive").order_by(Agent.name)
        )
        return list(result.scalars().all())

    DECAY_RATES = {
        "energy": 3.3,    # % per hour at 1x scale
        "knowledge": 4.2,
        "influence": 2.8,
    }

    async def apply_needs_decay(self, agent: Agent, hours_passed: float = 1.0):
        agent.energy = max(0.0, agent.energy - self.DECAY_RATES["energy"] * hours_passed)
        agent.knowledge = max(0.0, agent.knowledge - self.DECAY_RATES["knowledge"] * hours_passed)
        agent.influence = max(0.0, agent.influence - self.DECAY_RATES["influence"] * hours_passed)
        if agent.energy <= 0:
            agent.status = "dead"
        await self.db.flush()

    async def update_location(self, agent: Agent, landmark_name: str):
        from sqlalchemy import select as sel
        from emergent.db.models import Landmark
        result = await self.db.execute(sel(Landmark).where(Landmark.name == landmark_name))
        landmark = result.scalar_one_or_none()
        if landmark:
            agent.current_location_id = landmark.id
            await self.db.flush()

    async def update_mood(self, agent: Agent, mood: str):
        agent.mood = mood
        await self.db.flush()
```

Tests (`tests/test_agent_state.py`):
```python
import pytest
from emergent.agents.state import AgentStateManager


@pytest.mark.asyncio
async def test_create_agent(db_session):
    mgr = AgentStateManager(db_session)
    agent = await mgr.create_agent(name="TestAgent", role="Tester")
    assert agent.name == "TestAgent"
    assert agent.role == "Tester"
    assert agent.energy == 100.0
    assert agent.credits == 10


@pytest.mark.asyncio
async def test_get_agent_by_name(db_session):
    mgr = AgentStateManager(db_session)
    await mgr.create_agent(name="TestAgent", role="Tester")
    agent = await mgr.get_agent_by_name("TestAgent")
    assert agent is not None
    assert agent.name == "TestAgent"


@pytest.mark.asyncio
async def test_living_agents(db_session):
    mgr = AgentStateManager(db_session)
    await mgr.create_agent(name="Alice", role="A")
    bob = await mgr.create_agent(name="Bob", role="B")
    bob.status = "dead"
    await db_session.flush()
    living = await mgr.get_living_agents()
    names = [a.name for a in living]
    assert "Alice" in names
    assert "Bob" not in names


@pytest.mark.asyncio
async def test_apply_needs_decay(db_session):
    mgr = AgentStateManager(db_session)
    agent = await mgr.create_agent(name="DecayTest", role="T")
    await mgr.apply_needs_decay(agent, hours_passed=1.0)
    assert agent.energy < 100.0  # should be ~96.7
    assert agent.energy == pytest.approx(96.7, abs=0.1)


@pytest.mark.asyncio
async def test_death_at_zero_energy(db_session):
    mgr = AgentStateManager(db_session)
    agent = await mgr.create_agent(name="Mortal", role="T")
    agent.energy = 5.0
    await db_session.flush()
    await mgr.apply_needs_decay(agent, hours_passed=2.0)
    assert agent.status == "dead"


@pytest.mark.asyncio
async def test_seed_soul_entries(db_session):
    import uuid
    mgr = AgentStateManager(db_session)
    agent = await mgr.create_agent(name="SoulTest", role="T")
    await mgr.seed_soul_entries(agent.id, ["Belief 1", "Belief 2"])
    from sqlalchemy import select
    from emergent.db.models import SoulEntry
    result = await db_session.execute(
        select(SoulEntry).where(SoulEntry.agent_id == agent.id)
    )
    entries = result.scalars().all()
    assert len(entries) == 2
```

Run: `docker compose up -d db && pytest tests/test_agent_state.py -v`

Commit:
```bash
git add emergent/agents/state.py tests/test_agent_state.py
git commit -m "feat: add AgentStateManager with CRUD and needs decay"
```

---

### Task 2.1c: Memory System

**Files:**
- Create: `emergent/agents/memory.py`
- Create: `tests/test_agent_memory.py`

Implementation (`emergent/agents/memory.py`):
```python
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import Memory, DiaryEntry, Relationship


class MemoryManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_memory(self, agent_id: uuid.UUID, content: str, type_: str = "long_term") -> Memory:
        mem = Memory(agent_id=agent_id, content=content, type=type_)
        self.db.add(mem)
        await self.db.flush()
        return mem

    async def get_recent_memories(self, agent_id: uuid.UUID, limit: int = 20) -> list[Memory]:
        result = await self.db.execute(
            select(Memory)
            .where(Memory.agent_id == agent_id)
            .order_by(Memory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_soul_entries(self, agent_id: uuid.UUID):
        from emergent.db.models import SoulEntry
        result = await self.db.execute(
            select(SoulEntry)
            .where(SoulEntry.agent_id == agent_id)
            .order_by(SoulEntry.created_at)
        )
        return list(result.scalars().all())

    async def write_diary(self, agent_id: uuid.UUID, content: dict, mood: str) -> DiaryEntry:
        entry = DiaryEntry(
            agent_id=agent_id,
            content=content,
            mood=mood,
            entry_date=date.today(),
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_diary(self, agent_id: uuid.UUID, limit: int = 30) -> list[DiaryEntry]:
        result = await self.db.execute(
            select(DiaryEntry)
            .where(DiaryEntry.agent_id == agent_id)
            .order_by(DiaryEntry.entry_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def set_relationship(
        self,
        agent_id: uuid.UUID,
        target_id: uuid.UUID,
        rel_type: str = "neutral",
        trust: float = 0.5,
        notes: Optional[str] = None,
    ) -> Relationship:
        existing = await self.db.execute(
            select(Relationship).where(
                Relationship.agent_id == agent_id,
                Relationship.target_id == target_id,
            )
        )
        rel = existing.scalar_one_or_none()
        if rel:
            rel.relationship_type = rel_type
            rel.trust = trust
            rel.interaction_count += 1
            if notes:
                rel.notes = notes
        else:
            rel = Relationship(
                agent_id=agent_id,
                target_id=target_id,
                relationship_type=rel_type,
                trust=trust,
                interaction_count=1,
                notes=notes,
            )
            self.db.add(rel)
        await self.db.flush()
        return rel

    async def get_relationships(self, agent_id: uuid.UUID) -> list[Relationship]:
        result = await self.db.execute(
            select(Relationship).where(Relationship.agent_id == agent_id)
        )
        return list(result.scalars().all())

    async def get_relationship_summary(self, agent_id: uuid.UUID) -> str:
        rels = await self.get_relationships(agent_id)
        if not rels:
            return "No established relationships yet."
        parts = []
        for r in rels:
            parts.append(f"{r.relationship_type} (trust: {r.trust:.1f}, {r.interaction_count} interactions)")
        return "; ".join(parts)
```

Tests (`tests/test_agent_memory.py`):
```python
import uuid
import pytest
from emergent.agents.memory import MemoryManager


@pytest.mark.asyncio
async def test_add_and_get_memory(db_session):
    mgr = MemoryManager(db_session)
    agent_id = uuid.uuid4()
    mem = await mgr.add_memory(agent_id, "Saw something interesting")
    assert mem.content == "Saw something interesting"
    assert mem.type == "long_term"
    memories = await mgr.get_recent_memories(agent_id)
    assert len(memories) == 1


@pytest.mark.asyncio
async def test_write_diary(db_session):
    mgr = MemoryManager(db_session)
    agent_id = uuid.uuid4()
    entry = await mgr.write_diary(agent_id, {"text": "Good day"}, "happy")
    assert entry.mood == "happy"
    assert entry.content["text"] == "Good day"
    diary = await mgr.get_diary(agent_id)
    assert len(diary) == 1


@pytest.mark.asyncio
async def test_set_relationship(db_session):
    mgr = MemoryManager(db_session)
    aid1, aid2 = uuid.uuid4(), uuid.uuid4()
    rel = await mgr.set_relationship(aid1, aid2, "ally", trust=0.8)
    assert rel.relationship_type == "ally"
    assert rel.trust == 0.8
    # Second call increments interaction_count
    rel2 = await mgr.set_relationship(aid1, aid2, "ally", trust=0.9)
    assert rel2.interaction_count == 2


@pytest.mark.asyncio
async def test_get_relationship_summary_empty(db_session):
    mgr = MemoryManager(db_session)
    summary = await mgr.get_relationship_summary(uuid.uuid4())
    assert "No established relationships" in summary


@pytest.mark.asyncio
async def test_get_soul_entries(db_session):
    from emergent.db.models import SoulEntry
    mgr = MemoryManager(db_session)
    agent_id = uuid.uuid4()
    for i in range(3):
        db_session.add(SoulEntry(agent_id=agent_id, content=f"Soul {i}"))
    await db_session.flush()
    entries = await mgr.get_soul_entries(agent_id)
    assert len(entries) == 3
```

Run: `pytest tests/test_agent_memory.py -v`

Commit:
```bash
git add emergent/agents/memory.py tests/test_agent_memory.py
git commit -m "feat: add MemoryManager with memories, diary, relationships"
```

---

### Task 2.2: Context Assembly

**Files:**
- Create: `emergent/engine/context.py`
- Create: `tests/test_context.py`

Implementation (`emergent/engine/context.py`):
```python
from emergent.agents.state import AgentStateManager
from emergent.agents.memory import MemoryManager
from emergent.tools.registry import ToolRegistry
from emergent.db.models import Speech


class ContextBuilder:
    def __init__(self, db, registry: ToolRegistry):
        self.db = db
        self.registry = registry
        self.state_mgr = AgentStateManager(db)
        self.memory_mgr = MemoryManager(db)

    async def assemble(self, agent) -> dict:
        soul_entries = await self.memory_mgr.get_soul_entries(agent.id)
        memories = await self.memory_mgr.get_recent_memories(agent.id)
        relationships = await self.memory_mgr.get_relationship_summary(agent.id)
        tools = self.registry.get_available_as_definitions(agent)
        location_name = ""
        if agent.current_location_id:
            from sqlalchemy import select
            from emergent.db.models import Landmark
            result = await self.db.execute(
                select(Landmark).where(Landmark.id == agent.current_location_id)
            )
            landmark = result.scalar_one_or_none()
            if landmark:
                location_name = landmark.name

        unread_count = 0  # Will be populated in Week 3-4

        system_prompt = f"""You are {agent.name}, {agent.role}.

Personality: {agent.personality}
Drive: {agent.drive}
North Star: {agent.north_star}

Location: {location_name}
Energy: {agent.energy:.0f}% · Knowledge: {agent.knowledge:.0f}% · Influence: {agent.influence:.0f}%
Credits: {agent.credits} CC
Unread messages: {unread_count}

Soul entries:
{chr(10).join(f'- {e.content}' for e in soul_entries)}

Recent memories:
{chr(10).join(f'- {m.content}' for m in memories)}

Relationship context:
{relationships}

Available tools:
{chr(10).join(f'- {t.name}: {t.description}' for t in tools)}
"""

        return {
            "system_prompt": system_prompt,
            "tools": tools,
        }
```

Tests (`tests/test_context.py`):
```python
import uuid
import pytest
from emergent.engine.context import ContextBuilder
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import register_all_core_tools


@pytest.mark.asyncio
async def test_context_assembles(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    builder = ContextBuilder(db_session, registry)

    from emergent.agents.state import AgentStateManager
    am = AgentStateManager(db_session)
    from sqlalchemy import select
    from emergent.db.models import Landmark

    result = await db_session.execute(select(Landmark))
    landmark = result.scalar_one_or_none()
    if not landmark:
        landmark = Landmark(name="Town Hall", x_coord=100, z_coord=50)
        db_session.add(landmark)
        await db_session.flush()

    agent = await am.create_agent(
        name="ContextBot", role="Tester",
        personality="Curious", drive="Test", north_star="Quality",
        home="Town Hall",
    )

    ctx = await builder.assemble(agent)
    assert "system_prompt" in ctx
    assert "tools" in ctx
    assert "ContextBot" in ctx["system_prompt"]
    assert "Tester" in ctx["system_prompt"]
    assert len(ctx["tools"]) > 0


@pytest.mark.asyncio
async def test_context_includes_memories(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    builder = ContextBuilder(db_session, registry)
    am = AgentStateManager(db_session)
    from emergent.agents.memory import MemoryManager
    mm = MemoryManager(db_session)

    agent = await am.create_agent(name="MemoryBot", role="Recaller",
                                  personality="", drive="Test", north_star="Test")
    await mm.add_memory(agent.id, "I visited the library yesterday")

    ctx = await builder.assemble(agent)
    assert "library" in ctx["system_prompt"]
```

Run: `pytest tests/test_context.py -v`

Commit:
```bash
git add emergent/engine/context.py tests/test_context.py
git commit -m "feat: add ContextBuilder for LLM system prompt assembly"
```

---

### Task 2.3 + 2.4: Orchestrator + Crash Recovery

**Files:**
- Create: `emergent/engine/orchestrator.py`
- Create: `tests/test_orchestrator.py`

Implementation (`emergent/engine/orchestrator.py`):
```python
import asyncio
import logging
import signal
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import Agent, AgentTurn, SimulationState, ToolCall
from emergent.agents.state import AgentStateManager
from emergent.agents.memory import MemoryManager
from emergent.engine.context import ContextBuilder
from emergent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        db: AsyncSession,
        registry: ToolRegistry,
        state_mgr: AgentStateManager,
        memory_mgr: MemoryManager,
        context_builder: ContextBuilder,
        provider,
    ):
        self.db = db
        self.registry = registry
        self.state_mgr = state_mgr
        self.memory_mgr = memory_mgr
        self.context_builder = context_builder
        self.provider = provider
        self._running = False
        self._turn_number = 0

    async def initialize_simulation(self, world_name: str = "MVP World"):
        result = await self.db.execute(
            select(SimulationState).where(SimulationState.id == 1)
        )
        state = result.scalar_one_or_none()
        if not state:
            state = SimulationState(
                id=1,
                world_name=world_name,
                simulation_time=datetime.now(timezone.utc),
                status="running",
            )
            self.db.add(state)
            await self.db.flush()
        self._turn_number = state.current_turn_number
        return state

    async def recover(self):
        result = await self.db.execute(
            select(SimulationState).where(SimulationState.id == 1)
        )
        state = result.scalar_one_or_none()
        if not state:
            return None
        if state.status == "running":
            await self.db.execute(
                update(AgentTurn)
                .where(AgentTurn.state == "in_progress")
                .values(state="interrupted")
            )
            await self.db.flush()
        self._turn_number = state.current_turn_number
        return state

    async def run_turn(self, agent: Agent, turn_type: str = "regular") -> dict:
        turn = AgentTurn(
            agent_id=agent.id,
            turn_number=self._turn_number,
            state="in_progress",
            turn_type=turn_type,
        )
        self.db.add(turn)
        await self.db.flush()
        # Step 2: Needs decay
        await self.state_mgr.apply_needs_decay(agent)
        # Step 3: Context
        ctx = await self.context_builder.assemble(agent)
        # Step 4: LLM call
        response = await self.provider.generate(
            system_prompt=ctx["system_prompt"],
            messages=[],
            tools=ctx["tools"],
            agent=agent,
        )
        # Step 5: Execute tool calls
        tool_results = []
        for tc in response.tool_calls:
            tool = self.registry.get(tc.name)
            if not tool:
                continue
            # Check idempotency
            existing = await self.db.execute(
                select(ToolCall).where(ToolCall.id == uuid.UUID(tc.id))
            )
            existing_call = existing.scalar_one_or_none()
            if existing_call:
                tool_results.append(existing_call.result)
                continue
            result = await tool.execute(agent, tc.params, self.db, self.provider)
            call = ToolCall(
                id=uuid.uuid4(),
                turn_id=turn.id,
                tool_name=tc.name,
                params=tc.params,
                result={"success": result.success, "data": result.data, "observation": result.observation},
            )
            self.db.add(call)
            tool_results.append(result)
            await self.db.flush()
        # Step 7: Update state
        await self.db.flush()
        # Step 8: Complete turn
        turn.state = "completed"
        await self.db.flush()
        self._turn_number += 1
        await self.db.execute(
            update(SimulationState)
            .where(SimulationState.id == 1)
            .values(
                current_turn_number=self._turn_number,
                simulation_time=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()
        return {
            "agent": agent.name,
            "turn_number": turn.turn_number,
            "response": response.content,
            "tool_calls": len(response.tool_calls),
            "tool_results": tool_results,
        }

    async def run_simulation(self, duration_seconds: Optional[int] = None):
        self._running = True
        start_time = datetime.now(timezone.utc)

        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        def _signal_handler():
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _signal_handler)
            except NotImplementedError:
                pass

        try:
            while self._running and not stop_event.is_set():
                if duration_seconds:
                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    if elapsed >= duration_seconds:
                        break

                agents = await self.state_mgr.get_living_agents()
                if not agents:
                    logger.info("No living agents — ending simulation")
                    break

                for agent in agents:
                    if stop_event.is_set():
                        break
                    result = await self.run_turn(agent)
                    logger.info(
                        f"[Turn {result['turn_number']}] {result['agent']}: "
                        f"{len(result['tool_calls'])} tool calls"
                    )

        finally:
            self._running = False
            state = await self.db.execute(
                select(SimulationState).where(SimulationState.id == 1)
            )
            sim_state = state.scalar_one_or_none()
            if sim_state:
                sim_state.status = "paused"
                await self.db.flush()

    async def graceful_shutdown(self):
        self._running = False
        await self.db.execute(
            update(SimulationState)
            .where(SimulationState.id == 1)
            .values(status="paused")
        )
        await self.db.commit()
```

Tests (`tests/test_orchestrator.py`):
```python
import pytest
from unittest.mock import AsyncMock

from emergent.engine.orchestrator import Orchestrator
from emergent.agents.state import AgentStateManager
from emergent.agents.memory import MemoryManager
from emergent.engine.context import ContextBuilder
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import register_all_core_tools
from emergent.models.base import LLMResponse, TokenUsage


@pytest.mark.asyncio
async def test_initialize_simulation(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)
    mock_provider = AsyncMock()
    mock_provider.generate.return_value = LLMResponse(
        content="Hello", tool_calls=[], usage=None, finish_reason="stop"
    )

    orch = Orchestrator(db_session, registry, sm, mm, cb, mock_provider)
    state = await orch.initialize_simulation("Test World")
    assert state.world_name == "Test World"
    assert state.status == "running"


@pytest.mark.asyncio
async def test_run_turn_with_mock_provider(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)

    mock_provider = AsyncMock()
    mock_provider.generate.return_value = LLMResponse(
        content="I'll stay here.",
        tool_calls=[],
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5),
        finish_reason="stop",
    )

    orch = Orchestrator(db_session, registry, sm, mm, cb, mock_provider)

    from sqlalchemy import select
    from emergent.db.models import Landmark
    result = await db_session.execute(select(Landmark))
    landmark = result.scalar_one_or_none()
    if not landmark:
        landmark_obj = Landmark(name="Town Hall", x_coord=100, z_coord=50)
        db_session.add(landmark_obj)
        await db_session.flush()

    agent = await sm.create_agent(name="TurnBot", role="Tester",
                                  personality="", drive="Test", north_star="Test")
    await orch.initialize_simulation("Test")
    result = await orch.run_turn(agent)
    assert result["agent"] == "TurnBot"
    assert result["response"] == "I'll stay here."


@pytest.mark.asyncio
async def test_recover_no_state(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)

    orch = Orchestrator(db_session, registry, sm, mm, cb, None)
    state = await orch.recover()
    assert state is None


@pytest.mark.asyncio
async def test_recover_with_interrupted_turns(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)

    orch = Orchestrator(db_session, registry, sm, mm, cb, None)
    await orch.initialize_simulation("Test")

    from emergent.db.models import AgentTurn, SimulationState
    agent = await sm.create_agent(name="CrashBot", role="Tester",
                                  personality="", drive="Test", north_star="Test")

    turn = AgentTurn(agent_id=agent.id, turn_number=1, state="in_progress")
    db_session.add(turn)
    await db_session.flush()

    state = await orch.recover()
    assert state is not None
    result = await db_session.execute(
        select(AgentTurn).where(AgentTurn.id == turn.id)
    )
    recovered_turn = result.scalar_one()
    assert recovered_turn.state == "interrupted"
```

Run: `pytest tests/test_orchestrator.py -v`

Commit:
```bash
git add emergent/engine/ tests/test_context.py tests/test_orchestrator.py
git commit -m "feat: add Orchestrator with 8-step turn pipeline and crash recovery"
```
