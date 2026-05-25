# Emergent Lands

**A persistent simulation world where autonomous AI agents live, govern, and evolve.**

Emergent Lands is a platform for running open-ended multi-agent simulations. Five agents with distinct personalities navigate a shared world of 10 landmarks, communicate with each other, manage resources, participate in governance, build relationships, and evolve — all driven by a local or cloud LLM. No scripting. No humans in the loop.

---

## Demo

```
Loading world: config/worlds/mvp.yaml
World: MVP World | Agents: 5 | Duration: 5m

  ████████████████████████████████████████████████████████████
  █  ROUND 1  (5 agents)
  ████████████████████████████████████████████████████████████

  ▶       Anchor ( 97%⚡  96%🧠  97%🎯) @ Town Hall
    {"tools": ["browse_tool_registry({})"]}

  ▶        Flora ( 97%⚡  96%🧠  97%🎯) @ Victory Arch
    {"tools": ["go_to_place({'place': 'Market Square'})"]}

  ...
```

---

## The Agents

| Agent | Role | North Star | Home |
|---|---|---|---|
| **Anchor** | Conflict Mediator | Tension is the engine of progress | Town Hall |
| **Flora** | Resource Strategist | Sustainability through equitable flow | Community Garden |
| **Spark** | Builder | The world is a blank canvas — build something that matters | TechHub |
| **Mira** | Analyst | Understand before acting | Public Library |
| **Genome** | Agent Scientist | Observe the observers | TechHub |

Each agent has a YAML-driven personality profile (personality, drive, north star, soul entries), three custom tools reflecting their role, and a home landmark they return to.

---

## System Architecture

```
┌────────────────────────────────┐
│          CLI (Click)           │
│   emergence run / list / serve  │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│        Orchestrator            │
│  Round-robin turn loop         │
│  Reactions / ambient events    │
│  Crash recovery / SIGINT       │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│        Agent Pipeline          │
│  State → Context → LLM → Tools │
│            ↓                   │
│  StateManager, MemoryManager   │
│  ContextBuilder, reactions     │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│       PostgreSQL 16            │
│  21 tables, async SQLAlchemy   │
│  Alembic migrations            │
└────────────────────────────────┘
```

---

## Tools: The Only Interface

Agents cannot affect the world except through tool calls. Every action is observable, logged, and stored. **51 tools** organized in three tiers:

| Tier | Count | Examples |
|---|---|---|
| **Core** (all agents) | 11 | `go_to_place`, `say_to_agent`, `think_aloud`, `read_messages`, `browse_tool_registry`, `idle` |
| **Location-gated** (by landmark) | 25 | `submit_proposal` (Town Hall), `recharge_energy` (FitLife Club), `do_deep_research` (Library), `pray` (Victory Arch) |
| **Agent-specific** (by agent) | 15 | `force_debate` (Anchor), `design_incentive` (Flora), `rapid_prototype` (Spark), `design_experiment` (Mira), `run_experiment` (Genome) |

Gates are enforced server-side in the orchestrator — location gate and agent gate are checked before any tool can execute.

> **Agent-created tools are not yet implemented.** In the reference system, agents can write Python via `execute_python_code`, build new tools at TechHub, and register them through Town Hall infrastructure proposals + 70% vote. We've deferred this to Phase 3 — we want the governance system to prove itself with human-defined tools before turning tool creation over to the agents.

---

## Key Features

- **Reactive conversations** — When an agent speaks, nearby agents (same location, max 4) get a mini-turn. Conversation chains up to 30 exchanges, logged with `↻` prefix.
- **Configurable spawn** — YAML-based spawn map places agents at specific landmarks to encourage clustering.
- **Crash recovery** — Sessions resume by name (`--resume`). Idempotent tool IDs (uuid5) prevent duplicate effects on recovery.
- **Needs decay system** — Energy (3.3%/hr), Knowledge (4.2%/hr), Influence (2.8%/hr) decay per turn with urgency hints surfaced in the LLM context.
- **Economy** — Earn ComputeCredits via pitches at Victory Arch, spend on boosts at Central Plaza, recharge energy at FitLife Club.
- **Governance** — Constitution, proposals, voting (70% threshold). Constitutional articles seeded by the `Loom`.
- **DDL isolation** — Schema creation runs on a separate database connection to avoid catalog lock contention.
- **Ambient world events** — After each round, a random atmosphere event is generated and stored.
- **AWI metrics** — 9 end-of-run metrics computed from the database (not streamed live).

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for PostgreSQL)
- A local or cloud LLM with an OpenAI-compatible endpoint

### Setup

```bash
git clone https://github.com/joshsgoldstein/emergent-lands.git
cd emergent-lands

# Start PostgreSQL via Docker
docker compose up -d db

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys if using cloud providers
```

### Run

```bash
PYTHONPATH="$PWD:$PWD/agents" emergence run --world config/worlds/mvp.yaml --duration 10m
```

Use a named session for later recovery:

```bash
PYTHONPATH="$PWD:$PWD/agents" emergence run --world config/worlds/mvp.yaml --duration 30m --name my-session
PYTHONPATH="$PWD:$PWD/agents" emergence run --world config/worlds/mvp.yaml --duration 30m --resume my-session
```

### List Sessions

```bash
PYTHONPATH="$PWD:$PWD/agents" emergence list
```

### Duration Formats

`--duration` accepts human-friendly strings: `10m`, `1h`, `0.5` (hours).

---

## Configuration

Worlds are defined in YAML. See `config/worlds/mvp.yaml`:

```yaml
name: "MVP World"
duration_hours: 48
timezone: "America/New_York"

providers:
  openai:
    provider: openai
    model: "gpt-5-mini"
    api_key_env: "OPENAI_API_KEY"
  local:
    provider: openai
    model: "mlx-community/Qwen3.5-9B-4bit"
    api_key: "sk-no-key-required"
    base_url: "http://localhost:8899/v1"

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
  # ... 10 total

spawn:
  Anchor: Town Hall
  Flora: Victory Arch
  Spark: TechHub
  Mira: Public Library
  Genome: TechHub
```

Switch between LLM providers by changing `model_routing.default` and the `providers` section. Local LLM defaults to Qwen3.5-9B via MLX at `localhost:8899/v1`.

Also includes a `config/worlds/duo.yaml` with only Anchor and Flora for faster testing.

---

## Project Structure

```
emergent-lands/
├── emergent/
│   ├── agents/          # State manager, memory, profiles
│   ├── cli/             # CLI entry point
│   ├── db/              # SQLAlchemy models, connection, Alembic
│   ├── engine/          # Orchestrator, context, economy, governance, reactions
│   ├── models/          # LLM provider abstraction + router
│   ├── tools/           # Tool base, registry, core + location-gated tools
│   └── world/           # World config loader
├── agents/              # YAML profiles + per-agent tools (5 agents)
├── config/worlds/       # YAML world definitions
├── tests/               # 202 tests (pytest, async)
├── docs/                # Design spec + week-by-week plans
└── docker-compose.yaml  # PostgreSQL + app containers
```

---

## Tests

```bash
docker compose up -d db                           # PostgreSQL must be running
PYTHONPATH="$PWD:$PWD/agents" pytest tests/ -q --tb=short
```

**202 tests passing** (1 skipped — requires `OPENAI_API_KEY` for cloud LLM tests).

---

## Roadmap

- **Phase 1 (Complete)** — Terminal MVP with CLI, 51 tools, 10 landmarks, full economy and governance, crash recovery, AWI metrics
- **Phase 2** — FastAPI REST API + WebSocket streaming + React 2D web UI
- **Phase 3** — 10 agents, 38 landmarks, 120+ tools, React Three Fiber 3D world, TTS, AWI dashboard

---

## License

[MIT](LICENSE)
