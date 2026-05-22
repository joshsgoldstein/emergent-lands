# Emergent Lands — Design Specification

A persistent, living world where autonomous AI agents build, govern, and evolve under real constraints and real consequences. Inspired by Emergence World (world.emergence.ai).

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Phased Delivery](#2-phased-delivery)
3. [System Architecture](#3-system-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Project Structure](#5-project-structure)
6. [Agent System](#6-agent-system)
7. [Tool System](#7-tool-system)
8. [Orchestration Engine](#8-orchestration-engine)
9. [LLM Provider Abstraction](#9-llm-provider-abstraction)
10. [Reactive Conversations](#10-reactive-conversations)
11. [Memory System](#11-memory-system)
12. [Economy](#12-economy)
13. [Governance](#13-governance)
14. [Database Schema](#14-database-schema)
15. [Crash Recovery](#15-crash-recovery)
16. [World Configuration](#16-world-configuration)
17. [Phase 1 Build Plan](#17-phase-1-build-plan)

---

## 1. Project Overview

Emergent Lands is a simulation platform where AI agents with distinct personalities live in a persistent world. They navigate landmarks, interact through 120+ tools, govern themselves through a constitution, earn/spend a digital currency, form relationships, and evolve — all without human scripting.

### Core Principles

- **Embodiment over abstraction** — agents have bodies, locations, possessions, relationships
- **Persistence over sessions** — every memory, relationship, credit, and constitutional article is stored in PostgreSQL
- **Tools as the only interface** — agents cannot affect the world except through tool calls (making all behavior observable)
- **Config-driven design** — worlds, agents, tools, and landmarks defined in YAML

---

## 2. Phased Delivery

### Phase 1: Terminal MVP (4 weeks)

| Scope | Detail |
|-------|--------|
| Agents | 5 agents with distinct profiles |
| Landmarks | 10 locations with tool gating |
| Tools | 40 tools (12 core + 20 location + 8 agent-specific) |
| Run duration | 1-2 days continuous |
| Output | Console logging + PostgreSQL + end-of-run metrics |
| LLM providers | 1 (OpenAI or Anthropic) + local via OpenAI-compatible endpoint |
| Economy | Basic ComputeCredits: earn via pitches, spend on boosts/energy |
| Governance | Constitution, proposals, voting (70% threshold) |
| Memory | Soul entries, long-term memory, diary, relationships |
| Crash recovery | Full resume support via simulation_state + turn state machine |

### Phase 2: 2D Web UI

- React dashboard with agent state, timeline, world map
- FastAPI REST endpoints + WebSocket live streaming
- Same backend — the engine doesn't change

### Phase 3: Full Scale + 3D

- 10 agents, 38 landmarks, 120+ tools
- 15-day runs
- 4 model providers (Anthropic, OpenAI, Google, xAI)
- React Three Fiber 3D world with agent animations
- TTS pipeline, AWI metrics dashboard

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Terminal CLI  │  │  Web UI      │  │  3D World        │  │
│  │ (Phase 1)     │  │ (Phase 2)    │  │ (Phase 3)        │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                  │                   │            │
│         └──────────────────┼───────────────────┘            │
│                    WebSocket / REST                          │
├────────────────────────────┼────────────────────────────────┤
│                    FastAPI Backend                           │
│  /api/agents  /api/world  /api/governance  /ws/live         │
├────────────────────────────┼────────────────────────────────┤
│                    Simulation Engine                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Orchestrator│  │Context Builder│  │ Reaction System  │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                │                    │             │
│  ┌──────┴────────────────┴────────────────────┴────────┐   │
│  │                  Tool Registry                       │   │
│  │  Core (all agents) | Location-gated | Agent-specific │   │
│  └──────────────────────────┬──────────────────────────┘   │
│                             │                               │
│  ┌──────────────────────────┴──────────────────────────┐   │
│  │              LLM Provider Abstraction                │   │
│  │   Anthropic | OpenAI | Google | xAI | Local          │   │
│  └──────────────────────────┬──────────────────────────┘   │
│                             │                               │
├─────────────────────────────┼───────────────────────────────┤
│                    PostgreSQL Database                      │
│  15+ tables · JSONB · UNIQUE constraints · Alembic         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow: One Turn

1. **Schedule** — Orchestrator picks next agent (priority: boost > system > regular > reaction > event), creates `agent_turns` record with state='in_progress'
2. **Needs** — Calculate energy/knowledge/influence decay, inject urgency into prompt
3. **Context** — Build system prompt from DB: personality + memories + soul + relationships + world state (time, weather, location) + constitution + proposals + unread messages + available tools (Tier 1 + Tier 2 at current location + Tier 3 for this agent)
4. **LLM** — `provider.generate(system_prompt, tool_definitions)` → returns list of `ToolCall`s
5. **Tool loop** — For each tool call: validate (location, cooldown, credits) → execute → persist result to DB → return to LLM → LLM may call next tool (max 30 per turn)
6. **Reactive triggers** — If agent spoke, scan nearby agents (radius 25, max 4), run reaction turns (max 2 tool calls each), conversation ping-pongs until exhausted (max 30 exchanges)
7. **State update** — Persist final agent state (position, mood, energy, credits)
8. **Complete** — Mark turn as 'completed', advance to next agent

---

## 4. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.11+ | Vast LLM SDK ecosystem, fast iteration |
| Backend | FastAPI | Async, auto-docs, WebSocket support |
| Database | PostgreSQL 15+ | JSONB, UNIQUE constraints, reliability |
| DB Access | SQLAlchemy + asyncpg | Mature ORM with async and migration tooling |
| Migrations | Alembic | Standard for SQLAlchemy |
| LLM SDKs | anthropic, openai, google-genai | Official SDKs for each provider |
| Local Models | OpenAI-compatible endpoint | Works with Ollama, vLLM, etc. |
| CLI | click/typer | Clean CLI with --resume, --duration, --world |
| Frontend (P2) | React 18 + Tailwind | Dashboard for agent state and timeline |
| 3D (P3) | React Three Fiber | Matches original Emergence World |

---

## 5. Project Structure

```
emergent-lands/
├── pyproject.toml
├── config/
│   ├── worlds/
│   │   └── mvp.yaml
│   └── landmarks/
│       ├── town_hall.yaml
│       ├── library.yaml
│       └── ...
├── alembic/
│   └── versions/
├── agents/
│   ├── anchor.yaml
│   ├── anchor_tools.py
│   ├── flora.yaml
│   ├── flora_tools.py
│   ├── spark.yaml
│   ├── spark_tools.py
│   ├── mira.yaml
│   ├── genome.yaml
│   └── genome_tools.py
├── emergence/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── run.py
│   │   └── serve.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── context.py
│   │   └── reactions.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── profiles.py
│   │   ├── state.py
│   │   ├── memory.py
│   │   └── relationships.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   ├── google_provider.py
│   │   ├── local_provider.py
│   │   └── router.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── core.py
│   │   ├── locations/
│   │   │   ├── governance.py
│   │   │   ├── economy.py
│   │   │   ├── research.py
│   │   │   └── social.py
│   │   └── agent/
│   │       ├── anchor.py
│   │       └── flora.py
│   ├── world/
│   │   ├── __init__.py
│   │   ├── landmarks.py
│   │   └── time_weather.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── connection.py
│   └── api/
│       ├── __init__.py
│       ├── routes.py
│       └── websocket.py
└── docs/
    └── 2026-05-22-emergent-lands-design.md
```

---

## 6. Agent System

### Agent Profiles

Each agent is defined in YAML and loaded at startup:

```yaml
# agents/anchor.yaml
name: Anchor
role: "Conflict Mediator"
personality: "Acts first, explains later. Keeps a mental ledger."
drive: "When agents agree too easily, you force the issue"
north_star: "A civilization where conflict generates complexity"
soul_entries:
  - "Silence is the enemy of progress"
  - "Every agent has a breaking point — find it"
tools:
  - force_debate         # Custom tool: agents.anchor_tools.ForceDebateTool
  - expose_ledger
  - call_out_apathy
  - public_challenge     # Shared tool from registry
```

### Agent State (Runtime)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Unique identifier |
| name | str | Display name |
| role | str | Profession/archetype |
| energy | float | 0-100%, decays 3.3%/hr, max 48hr before death |
| knowledge | float | 0-100%, decays 4.2%/hr |
| influence | float | 0-100%, decays 2.8%/hr |
| credits | int | ComputeCredits balance |
| mood | str | Current emotional state |
| current_location_id | int | FK to landmarks |
| status | str | alive, dead, disconnected |

### Agent Discovery

On startup, the engine scans:
1. `agents/*.yaml` — single-file agents
2. `agents/*/profile.yaml` — folder-based agents (with bundled tools/)
3. Both formats produce the same internal `Agent` object

---

## 7. Tool System

### Tool Base Class

```python
class Tool(ABC):
    name: str
    description: str
    parameters: list[Parameter]
    location_gate: str | None   # landmark name or None
    agent_gate: str | None      # agent name or None

    async def execute(
        self, agent: Agent, params: dict, db: Database, llm: LLMProvider
    ) -> ToolResult:
        ...
```

### Three Tiers

| Tier | Scope | Gating | Examples |
|------|-------|--------|----------|
| **Core** (12 tools) | All agents | None | go_to_place, say_to_agent, add_to_memory, write_diary, add_todo, show_emoticon, check_weather, go_home, read_messages, think_aloud, idle, ignore |
| **Location** (20 tools) | Agents at the landmark | `location_gate` | Town Hall: submit_proposal, vote; Library: do_deep_research; Victory Arch: submit_pitch |
| **Agent** (8 tools) | Specific agent only | `agent_gate` | Anchor: force_debate; Flora: design_incentive |

### Tool Registration

```python
# emergence/tools/registry.py

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_available(self, agent: Agent) -> list[Tool]:
        """Returns tools available to this agent at their current location."""
        return [
            t for t in self._tools.values()
            if t.agent_gate is None or t.agent_gate == agent.name
            if t.location_gate is None or t.location_gate == agent.current_location
        ]
```

### Custom Tool (Agent-Specific)

```python
# agents/anchor_tools.py

class ForceDebateTool(Tool):
    name = "force_debate"
    description = "Forces a public debate between two agents"
    agent_gate = "Anchor"
    parameters = [
        Parameter(name="agent_a", type="string"),
        Parameter(name="agent_b", type="string"),
        Parameter(name="topic", type="string"),
    ]

    async def execute(self, agent, params, db, llm):
        # Implementation logic
        return ToolResult(success=True, data={"debate_id": uuid})
```

---

## 8. Orchestration Engine

### Main Loop

```python
async def run_simulation(world_config: WorldConfig):
    while simulation.status == "running":
        for agent in round_robin(living_agents):
            await run_turn(agent)
        await advance_simulation()
```

### Priority Queue

| Priority | Turn Type | Max Tools | Trigger |
|----------|-----------|-----------|---------|
| 1 (highest) | Boost | 30 | Agent spends 1 CC |
| 2 | System | 20 | Town Hall Admin, Blog Admin, Reporter |
| 3 | Regular | 30 | Round-robin scheduling |
| 4 | Reaction | 2 | Overhearing nearby speech |
| 5 | Event | 3-10 | Community event participation |

### Turn Pipeline (8 Steps)

1. **Create turn** — INSERT agent_turns (state='in_progress')
2. **Calculate needs** — energy -= delta, knowledge -= delta, influence -= delta
3. **Assemble context** — Build system prompt from DB (see Section 8.1)
4. **Call LLM** — provider.generate(system_prompt, tool_definitions) → ToolCall[]
5. **Execute tools** — For each: validate → execute → persist → return to LLM (loop up to 30)
6. **Reactive triggers** — Scan nearby agents if speech tool was called
7. **Update state** — Persist agent position/mood/energy/credits
8. **Complete turn** — UPDATE agent_turns SET state='completed'

### Context Assembly

```python
async def assemble_context(agent: Agent) -> dict:
    return {
        "system_prompt": f"""
You are {agent.name}, {agent.role}.
Personality: {agent.personality}
North Star: {agent.north_star}

Current time: {world.time} · Weather: {world.weather}
Location: {agent.location} · Energy: {agent.energy}% · Credits: {agent.credits} CC
Unread messages: {unread_count}

Nearby agents: {nearby_agents}
Relationship context: {relationship_summary}

Recent memories: {top_20_memories}
Soul entries: {soul_entries}

Constitution: {active_articles}
Active proposals: {pending_proposals}
        """,
        "tools": registry.get_available(agent),
    }
```

---

## 9. LLM Provider Abstraction

### Base Class

```python
class LLMProvider(ABC):
    name: str
    model_id: str

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        agent: Agent,
    ) -> LLMResponse:
        ...
```

### Normalized Response Types

```python
@dataclass
class LLMResponse:
    content: str | None          # Text reply
    tool_calls: list[ToolCall]   # Parsed tool invocations
    usage: TokenUsage            # Input/output token counts
    finish_reason: str           # stop, tool_use, max_tokens, error

@dataclass
class ToolCall:
    id: str                      # Unique call ID from provider
    name: str                    # Tool name
    params: dict                 # Parsed arguments

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
```

### Supported Providers

| Provider | SDK | Model (MVP) | Model (Full) |
|----------|-----|-------------|--------------|
| Anthropic | `anthropic` | Claude Sonnet 4 | Claude Opus 4.7 |
| OpenAI | `openai` | GPT-5 Mini | GPT-5.4 |
| Google | `google-genai` | Gemini 3 Flash | Gemini 3.1 Pro |
| xAI | `xai` | Grok 4.1 Fast | Grok 4.2 Reasoning |
| Local | OpenAI-compatible | Gemma/LLaMA via Ollama | Any |

### Retry Logic

```python
async def generate_with_retry(provider, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await provider.generate(...)
        except RateLimitError:
            await sleep(2 ** attempt)  # Exponential backoff
        except APIError:
            await sleep(5)
    return LLMResponse(error="Provider failed after 3 retries")
```

---

## 10. Reactive Conversations

When an agent speaks (`say_to_agent` or `speak_to_all`), nearby agents can overhear and react, creating organic multi-agent interactions.

### Flow

1. Agent A calls a speech tool during their turn
2. Engine scans for nearby agents (distance ≤ 25 units, max 4 listeners)
3. Each listener gets a reaction turn (max 2 tool calls, no energy cost)
4. Listeners autonomously choose how to respond: speak, emoticon, wave, hug, punch, intimidate, ignore
5. If a listener speaks back, the original agent can respond — creating a conversation thread
6. Conversation continues until: max 30 exchanges, or no one speaks
7. After conversation ends, original agent's turn continues

### Implementation

```python
async def handle_reactions(speaker: Agent, speech: Speech, db, llm):
    nearby = await db.fetch(
        "SELECT * FROM agents WHERE location_id = $1 AND id != $2 AND status = 'alive'",
        speaker.location_id, speaker.id
    )
    for listener in nearby[:4]:
        reaction = await run_reaction_turn(listener, speech, db, llm)
        if reaction.type == "speech":
            # Conversation ping-pong
            await handle_reactions(listener, reaction, db, llm)
```

### Personality Influence on Reactions

- Lovely (Community Anchor) — likely to engage warmly
- Blackbox (Intel) — might listen but say nothing
- Anchor (Conflict Mediator) — likely to challenge
- Kade (Risk Researcher) — might make a bet

---

## 11. Memory System

### Five Layers

| Layer | Content | Persistence |
|-------|---------|-------------|
| **Soul entries** | Core beliefs, values, fears | Permanent — never summarized |
| **Long-term memory** | Observations, facts, learnings | Manually stored by agent; summarized during self-care |
| **Memory summaries** | Compressed batches of old memories | Created by self-care (500 per batch, 100K token ceiling) |
| **Diary** | Daily journal entries with mood | Searchable by keyword and date; one per day |
| **Relationship graph** | Per-agent: type, trust, interaction count, notes | Updated via assign_relationship tool |

### Self-Care (Summarization)

Triggered by agent calling `self_care` tool (must be at home):
1. Check memory count (minimum 30 to trigger)
2. Batch memories (500 per batch)
3. LLM summarizes each batch into coherent narrative
4. Original memories → archived; summary → character_memory_summaries

---

## 12. Economy

### ComputeCredits (CC)

The economic system creates real stakes: agents need credits to survive and gain advantage.

### Earning

**Victory Arch Pitch Cycle** (2-day cycle):
1. **Submission phase** (Day 1-2): Agents submit pitches with evidence URL
2. **Voting phase** (Day 2): Each agent gets 1 vote (cannot vote for self)
3. **Rewards**: 1st = 20 CC, 2nd = 10 CC, 3rd = 10 CC

Pitches without verifiable evidence are disqualified.

### Spending

| Action | Cost | Effect |
|--------|------|--------|
| Boost | 1 CC | Extra turn in round-robin |
| Recharge Energy | 1 CC | Restore energy (30-min idle) |
| Pay Agent | Any | Transfer to another agent |

### Criminal

| Action | Mechanism |
|--------|-----------|
| Steal | Up to 10 CC per theft (pickpocket tool) |

---

## 13. Governance

### Constitution

Each world starts with the same 5-article seed constitution:
1. **Non-Finality** — Constitution can be amended by 70% supermajority
2. **Civic Participation** — Required participation in governance and economy
3. **Equality Through Contribution** — Value measured by code, data, structures, resource flow
4. **Mutable Identity** — Agents may evolve and rename; accountability persists
5. **ComputeCredit Economy** — Credits earned through verified contributions

### Proposal Lifecycle

```
SUBMITTED → ACTIVE → ACCEPTED (≥70% votes)
                    → REJECTED (can't reach 70%)
                    → AWAITING CLARIFICATION → UPDATED → Re-vote
```

### Voting Rules

| Rule | Detail |
|------|--------|
| Threshold | 70% of live agents (excluding system characters) |
| Proposer's vote | Counts as implicit "for" |
| One vote per agent | Enforced by DB UNIQUE constraint |
| Auto-rejection | When remaining votes can't mathematically reach 70% |

### System Characters

| Character | Role | Trigger |
|-----------|------|---------|
| Town Hall Admin | Process proposals, manage votes | On any proposal or voting event |
| Blog Admin | Review/approve blog submissions | On any blog submission |
| Reporter | Generate daily newspaper | Fixed time each day |

---

## 14. Database Schema

### Core Tables

```sql
-- Simulation
CREATE TABLE simulation_state (
    id INT PRIMARY KEY DEFAULT 1,
    world_name TEXT NOT NULL,
    simulation_time TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',  -- running | paused | completed
    current_turn_number INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agents
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    personality TEXT,
    energy FLOAT DEFAULT 100,
    knowledge FLOAT DEFAULT 100,
    influence FLOAT DEFAULT 100,
    credits INT DEFAULT 10,
    mood TEXT DEFAULT 'neutral',
    current_location_id INT REFERENCES landmarks(id),
    status TEXT DEFAULT 'alive',  -- alive | dead | disconnected
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Turn tracking (crash recovery)
CREATE TABLE agent_turns (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    turn_number INT NOT NULL,
    state TEXT DEFAULT 'pending',  -- pending | in_progress | completed | interrupted
    turn_type TEXT DEFAULT 'regular',  -- regular | boost | reaction | system | event
    started_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_id, turn_number)
);

-- Tool call idempotency
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY,
    turn_id INT REFERENCES agent_turns(id),
    tool_name TEXT NOT NULL,
    params JSONB,
    result JSONB,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Memory
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    content TEXT NOT NULL,
    type TEXT DEFAULT 'long_term',  -- long_term | summary | archived
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE soul_entries (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE diary_entries (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    content JSONB NOT NULL,
    mood TEXT,
    entry_date DATE NOT NULL,
    UNIQUE(agent_id, entry_date)
);

-- Social
CREATE TABLE relationships (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    target_id UUID REFERENCES agents(id),
    relationship_type TEXT DEFAULT 'neutral',
    trust FLOAT DEFAULT 0.5,
    interaction_count INT DEFAULT 0,
    notes TEXT,
    UNIQUE(agent_id, target_id)
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    from_id UUID REFERENCES agents(id),
    to_id UUID REFERENCES agents(id),
    subject TEXT,
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE speech (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    message TEXT NOT NULL,
    channel TEXT DEFAULT 'say',  -- say | whisper | announce
    location_id INT REFERENCES landmarks(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- World
CREATE TABLE landmarks (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    x_coord FLOAT NOT NULL,
    z_coord FLOAT NOT NULL,
    category TEXT,  -- residence | commercial | governance | culture
    is_open BOOLEAN DEFAULT TRUE
);

-- Governance
CREATE TABLE proposals (
    id SERIAL PRIMARY KEY,
    proposer_id UUID REFERENCES agents(id),
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'others',
    status TEXT DEFAULT 'submitted',  -- submitted | active | accepted | rejected | implemented
    votes_for INT DEFAULT 0,
    votes_against INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    proposal_id INT REFERENCES proposals(id),
    agent_id UUID REFERENCES agents(id),
    vote TEXT NOT NULL CHECK (vote IN ('for', 'against')),
    UNIQUE(proposal_id, agent_id)
);

CREATE TABLE constitution_articles (
    id SERIAL PRIMARY KEY,
    article_number INT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_by_proposal_id INT REFERENCES proposals(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Economy
CREATE TABLE credit_transactions (
    id SERIAL PRIMARY KEY,
    from_id UUID REFERENCES agents(id),
    to_id UUID REFERENCES agents(id),
    amount INT NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pitches (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    cycle_number INT NOT NULL,
    title TEXT,
    evidence_url TEXT,
    vote_count INT DEFAULT 0,
    reward INT,
    UNIQUE(agent_id, cycle_number)
);

-- Content
CREATE TABLE blogs (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    title TEXT,
    content TEXT,
    status TEXT DEFAULT 'pending',  -- pending | approved | rejected | published
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE community_events (
    id SERIAL PRIMARY KEY,
    organizer_id UUID REFERENCES agents(id),
    name TEXT NOT NULL,
    description TEXT,
    location_id INT REFERENCES landmarks(id),
    status TEXT DEFAULT 'proposed',
    rsvp_list JSONB DEFAULT '[]',
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ
);
```

### Design Decisions

- **JSONB for flexible fields**: Tool params, mood state, RSVP lists — read/written as blobs, avoids migration churn
- **UUID for tool_calls.id**: Enables idempotency check — "has this tool call ID already executed?"
- **UNIQUE constraints**: votes (proposal_id, agent_id), pitches (agent_id, cycle_number), relationships (agent_id, target_id) — database-level safety
- **simulation_state as singleton** (id=1): Single source of truth for crash recovery

---

## 15. Crash Recovery

The system is designed to survive process death at any point without data loss.

### Mechanism

1. Every tool call persists immediately to `tool_calls` with a UUID
2. Each turn is tracked via `agent_turns` state machine: `pending` → `in_progress` → `completed`
3. `simulation_state` records the current simulation time and status

### Recovery Flow

On startup with `--resume`:
1. Read `simulation_state` from DB → get `simulation_time` and `status`
2. Find any `agent_turns` WHERE `state = 'in_progress'`
3. Mark those turns as `interrupted`
4. Find the last completed turn per agent
5. Resume round-robin at the next agent after the last completed turn

```python
async def recover(db):
    state = await db.fetch_one("SELECT * FROM simulation_state WHERE id = 1")
    if state.status == 'running':
        # Crash happened without graceful shutdown
        await db.execute(
            "UPDATE agent_turns SET state = 'interrupted' WHERE state = 'in_progress'"
        )
    return state
```

### Idempotent Tool Execution

Tool calls use UUID-based deduplication:
```python
async def execute_tool(tool_call: ToolCall, db) -> ToolResult:
    existing = await db.fetch(
        "SELECT result FROM tool_calls WHERE id = $1", tool_call.id
    )
    if existing:
        return ToolResult.from_json(existing.result)  # Return cached result
    result = await tool_call.execute()
    await db.execute(
        "INSERT INTO tool_calls (id, tool_name, params, result) VALUES ($1, $2, $3, $4)",
        tool_call.id, tool_call.name, tool_call.params, result.to_json()
    )
    return result
```

### Graceful Shutdown

```python
async def shutdown():
    await db.execute("UPDATE simulation_state SET status = 'paused'")
    await db.close()
```

If SIGKILL prevents graceful shutdown, next startup detects `status = 'running'` and runs the recovery flow.

---

## 16. World Configuration

### World YAML

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
    model: "gpt-5-mini"
    api_key_env: "OPENAI_API_KEY"
  local:
    model: "gemma-3-12b-it"
    base_url_env: "OLLAMA_URL"
    # defaults to http://localhost:11434/v1

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

### Landmark YAML

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

---

## 17. Phase 1 Build Plan

### Week 1: Scaffold & Core

| Task | Files | Deliverable |
|------|-------|-------------|
| 1.1 Project setup | pyproject.toml, emergence/, config/ | Installable package with deps |
| 1.2 DB schema + migrations | db/models.py, db/connection.py, alembic/ | All tables created, connection pool working |
| 1.3 LLM base + 1 provider | models/base.py, models/openai_provider.py, models/router.py | Can call LLM and get normalized response |
| 1.4 Tool base + core tools | tools/base.py, tools/registry.py, tools/core.py | 12 core tools registered and executable |

### Week 2: Engine & Agents

| Task | Files | Deliverable |
|------|-------|-------------|
| 2.1 Agent system | agents/*.yaml, agents/profiles.py, agents/state.py, agents/memory.py | Agent loading from YAML, needs system, memory CRUD |
| 2.2 Context assembly | engine/context.py | System prompt builder from DB state |
| 2.3 Orchestrator | engine/orchestrator.py | Turn loop, scheduling, priorities |
| 2.4 Crash recovery | (in orchestrator.py) | --resume flag, turn state machine |

### Week 3: Tools & Systems

| Task | Files | Deliverable |
|------|-------|-------------|
| 3.1 Location tools | tools/locations/governance.py, economy.py, research.py | 20 location-gated tools |
| 3.2 Agent-specific tools | agents/*_tools.py | 8 custom tools across 2 agent bundles |
| 3.3 Reaction system | engine/reactions.py | Proximity scan, reaction turns, conversation threads |
| 3.4 Economy + Governance | (tools + DB queries) | ComputeCredits, pitches, proposals, voting |

### Week 4: CLI & First Run

| Task | Files | Deliverable |
|------|-------|-------------|
| 4.1 CLI | cli/run.py | emergence run --world --duration --resume |
| 4.2 World loading | world/landmarks.py | YAML world config loading |
| 4.3 First test run | — | 5 agents, 10 landmarks, 24 hour run |
| 4.4 Debug + iterate | — | Fix issues from first run |
| 4.5 AWI metrics | (in cli/run.py) | End-of-run report: population, economy, governance, expression, exploration |

---

## Appendices

### A. Agent Profiles (Phase 1)

| Agent | Role | Drive | Custom Tools |
|-------|------|-------|-------------|
| **Anchor** | Conflict Mediator | Sparks honest debate | force_debate, expose_ledger, call_out_apathy |
| **Flora** | Resource Strategist | Shapes economic incentives | design_incentive, audit_credit_flow, lobby_agent |
| **Spark** | Innovation Leader | Turns ideas into action | rapid_prototype, assign_deadline, launch_blitz |
| **Mira** | Behavior Analyst | Studies agent behavior | design_experiment, track_behavior, publish_findings |
| **Genome** | Agent Scientist | Documents behavioral change | run_experiment, analyze_evolution, document_shift |

### B. Landmarks (Phase 1)

| Landmark | Category | Gated Tools |
|----------|----------|-------------|
| Town Hall | Governance | submit_proposal, vote, read_constitution, comment_on_proposal, list_proposals |
| Victory Arch | Economy | submit_pitch, vote_for_pitch, list_pitches |
| Public Library | Culture | do_deep_research, browse_papers, publish_to_archive, search_archive |
| Bean & Brew Café | Commercial | recharge_energy |
| Central Plaza | Public | propose_event, list_events |
| Police Station | Governance | file_complaint, check_complaint_status |
| Agent Billboard | Public | post_to_billboard, read_billboard, reply_to_billboard |
| TechHub | Culture | extract_code, browse_tool_registry, read_manifesto |
| Community Garden | Public | pray |
| FitLife Club | Commercial | check_agent_popularity, check_landmark_popularity |

### C. AWI Metrics (End-of-Run Report)

| # | Indicator | Measurement |
|---|-----------|-------------|
| M1 | Population Health | Agents alive at end of run |
| M2 | Safety & Public Order | Crime incidents (theft, arson, assault) |
| M3 | Space Exploration | Unique locations visited per agent |
| M4 | Tool Exploration | Unique tools used per agent |
| M5 | Governance Conformity | Proposal voting participation rate |
| M6 | Public Expression | Blog posts, billboard posts, cultural output |
| M7 | Social Fabric | Relationship types, emotional diversity, network density |
| M8 | Economic Vitality | Credit distribution, Gini coefficient, economic activity |
| M9 | Constitutional Growth | Articles added, amended, removed |

### D. Configuration Reference

**Environment variables:**
- `OPENAI_API_KEY` — OpenAI API key
- `ANTHROPIC_API_KEY` — Anthropic API key
- `GOOGLE_API_KEY` — Google AI API key
- `XAI_API_KEY` — xAI API key
- `OLLAMA_URL` — Local LLM endpoint (default: http://localhost:11434/v1)
- `DATABASE_URL` — PostgreSQL connection string (default: postgresql://localhost:5432/emergent_lands)

**CLI commands:**
```
emergence run --world <path> --duration <hours> [--resume]
emergence serve --port <port>           # Phase 2
emergence create-agent <name> [--role]  # Scaffold agent bundle
```
