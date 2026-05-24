# Emergent Lands — Project Status

```ascii
  █████████████████████████████████████████████████
  █  Phase 1 — Terminal MVP  █▣▣▣▣▣▣▣▣▣▣  100%
  █████████████████████████████████████████████████
  █  Phase 2 — API + Web UI  █░░░░░░░░░░    0%
  █████████████████████████████████████████████████
  █  Phase 3 — 3D World       █░░░░░░░░░░    0%
  █████████████████████████████████████████████████
```

## Commands

| Command | Description |
|---|---|
| `emergence run --world <path> --duration <str> [--resume <name>] [--name <str>]` | Run simulation |
| `emergence list` | List all sessions |
| `emergence serve` | API server (Phase 2 stub) |

`--duration` accepts `10m`, `1h`, `0.5` (float hours for backward compat).

## Architecture

**Stack:** Python 3.11+ / SQLAlchemy 2.0 async / PostgreSQL 16 Alpine / Docker Compose

**21 DB tables:** agents, agent_turns, landmarks, sessions, tool_calls, speech, memories, messages, soul_entries, world_events, proposals, votes, constitution_articles, pitches, credit_transactions, complaints, billboard_posts, community_events, relationships, diary_entries, blogs

**51 tools (3 tiers)**
- **11 core** (all agents): go_to_place, say_to_agent, think_aloud, read_messages, go_home, browse_tool_registry, write_diary, show_emoticon, check_weather, idle, ignore
- **25 location-gated**: governance (5: submit_proposal, vote_on_proposal, read_constitution, comment_on_proposal, list_proposals), economy (6: submit_pitch, vote_for_pitch, list_pitches, recharge_energy, pay_credits, boost_turn), research (4: do_deep_research, browse_papers, publish_to_archive, search_archive), social (10: propose_event, list_events, post_to_billboard, read_billboard, extract_code, browse_tool_registry, pray, check_agent_popularity, file_complaint, check_complaint_status)
- **15 agent-specific** (3 per agent, gated by agent_id): Anchor (force_debate, expose_ledger, call_out_apathy), Flora (design_incentive, audit_credit_flow, lobby_agent), Spark (rapid_prototype, assign_deadline, launch_blitz), Mira (design_experiment, track_behavior, publish_findings), Genome (run_experiment, analyze_evolution, document_shift)

## Agents

| Agent | Role | North Star | Home |
|---|---|---|---|
| Anchor | Conflict Mediator | "Tension is the engine of progress" | Town Hall |
| Flora | Resource Strategist | "Sustainability through equitable flow" | Community Garden |
| Spark | Builder | "The world is a blank canvas — build something that matters" | TechHub |
| Mira | Analyst | "Understand before acting" | Public Library |
| Genome | Agent Scientist | "Observe the observers" | TechHub |

Each agent has soul entries for behavior direction + 3 custom tools.

## Key Implementation Details

- **Reactions**: When an agent uses `say_to_agent`, nearby agents (same location, max 4) get a mini-turn (max 2 tools). Conversation chains up to 30 exchanges, logged with `↻` prefix.
- **Server-side gate validation**: Both `location_gate` and `agent_gate` checked in orchestrator before tool execution; agents cannot use tools from other locations or other agents' custom tools.
- **Deterministic idempotency**: ToolCall IDs use `uuid5(NAMESPACE_DNS, tc.id)` — same LLM call produces same UUID, enabling crash recovery without duplicate effects.
- **60s LLM timeout**: `asyncio.wait_for` wraps every LLM call; timeout produces empty response (no crash).
- **DDL isolation**: `Base.metadata.create_all` runs on its own engine connection before simulation starts, avoiding catalog lock contention.
- **Configurable spawn**: World YAML `spawn` dict maps agent names to landmark start positions; defaults to Central Plaza gathering.
- **Needs decay**: Energy 3.3%/hr, Knowledge 4.2%/hr, Influence 2.8%/hr, applied per-turn with urgency hints in context.
- **Prompt directive**: "Do NOT idle or just observe — take action" included in system prompt to discourage passive behavior.
- **AWI metrics**: 9 metrics computed from DB at end-of-run (not streamed live).
- **LLM providers**: OpenAI-compatible endpoint (local or cloud), swappable via ProviderRouter with env-based key resolution. Local default: `localhost:8899/v1` with Qwen3.5-9B-4bit.

## Phase 1 Completed

- [x] Scaffold: pyproject.toml, Docker Compose, SQLAlchemy models (21 tables), async DatabaseManager, Alembic
- [x] LLM: ProviderRouter, OpenAI provider, base provider
- [x] Tools: ABC, ToolRegistry, 51 tools across 3 tiers with server-side gating
- [x] World config: YAML loader, MVP and Duo world configs with spawn locations
- [x] Engine: Orchestrator (8-step turn pipeline, round-robin, ambient events)
- [x] Agents: 5 YAML profiles, AgentStateManager (CRUD, needs decay), MemoryManager, ContextBuilder
- [x] Economy: CreditManager, pitch system
- [x] Governance: GovernanceManager, proposals, constitution
- [x] Reactions: Proximity-scanning conversation chains (max 30 exchanges, max 4 listeners)
- [x] CLI: `emergence run`/`list`/`serve` with `--duration` (human-friendly strings), `--resume`, `--name`
- [x] Crash recovery: Sessions resume by name with `--resume`, interrupted turns marked, uuid5 idempotency
- [x] AWI metrics: 9 end-of-run metrics
- [x] DDL isolation on separate connection

## What's Next (Phase 2)

- API server (FastAPI) with REST endpoints
- Web UI (2D interactive world)
- Real-time streaming of simulation events via WebSocket

### Model Routing Ideas (Future)

Currently model routing is per-agent via `model_routing.overrides`. Extend to:

- **Per-landmark routing** — specific LLM used when agent is at a given landmark (e.g., Town Hall debates use a stronger model)
- **Per-activity routing** — specific LLM for certain tool categories (e.g., heavy reasoning tools use GPT, routine tools use local)
- **Inline per-agent config** — assign provider + model directly in the `agents` list instead of via separate overrides dict

## Tests

```text
202 passed, 1 skipped in 16.44s
```

(1 skip: requires OPENAI_API_KEY env var). Run with `pytest tests/ -q --tb=short`.

## Running

```bash
docker compose up -d db                                    # start PostgreSQL
PYTHONPATH="$PWD:$PWD/agents" emergence run --world config/worlds/mvp.yaml --duration 5m
PYTHONPATH="$PWD:$PWD/agents" emergence run --world config/worlds/mvp.yaml --duration 10m --name my-session
PYTHONPATH="$PWD:$PWD/agents" emergence run --world config/worlds/mvp.yaml --duration 10m --resume my-session
PYTHONPATH="$PWD:$PWD/agents" emergence list
```

Local LLM endpoint at `http://localhost:8899/v1` (OpenAI-compatible), model `mlx-community/Qwen3.5-9B-4bit`.
