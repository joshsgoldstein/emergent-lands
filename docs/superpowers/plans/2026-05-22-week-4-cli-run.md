# Week 4: CLI & First Run

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** Wire everything together into a working CLI that loads a world, seeds agents, and runs a simulation with end-of-run AWI metrics.

---

### Task 4.1: CLI Entry Point

**Files:**
- Create: `emergent/cli/run.py`
- Create: `emergent/cli/__init__.py` (update)
- Create: `tests/test_cli.py`

Implementation (`emergent/cli/run.py`):
```python
import asyncio
import logging
import os
import sys

import click

from emergent.db.connection import DatabaseManager, get_database_url
from emergent.db.base import Base
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import register_all_core_tools
from emergent.tools.locations.governance import (
    SubmitProposalTool, VoteOnProposalTool, ReadConstitutionTool,
    CommentOnProposalTool, ListProposalsTool,
)
from emergent.tools.locations.economy import (
    SubmitPitchTool, VoteForPitchTool, ListPitchesTool,
    RechargeEnergyTool, PayCreditsTool, BoostTurnTool,
)
from emergent.tools.locations.research import (
    DoDeepResearchTool, BrowsePapersTool, PublishToArchiveTool, SearchArchiveTool,
)
from emergent.tools.locations.social import (
    ProposeEventTool, ListEventsTool, PostToBillboardTool, ReadBillboardTool,
    ExtractCodeTool, BrowseToolRegistryTool, PrayTool,
    CheckAgentPopularityTool, FileComplaintTool, CheckComplaintStatusTool,
)
from emergent.agents.state import AgentStateManager
from emergent.agents.memory import MemoryManager
from emergent.agents.profiles import discover_agents, load_agent_profile
from emergent.engine.context import ContextBuilder
from emergent.engine.orchestrator import Orchestrator
from emergent.engine.economy import CreditManager
from emergent.engine.governance import GovernanceManager
from emergent.models.router import ProviderRouter, ProviderConfig
from emergent.world.config import load_world_config

logger = logging.getLogger(__name__)


def build_registry():
    registry = ToolRegistry()
    register_all_core_tools(registry)
    # Location tools
    for tool in [
        SubmitProposalTool(), VoteOnProposalTool(), ReadConstitutionTool(),
        CommentOnProposalTool(), ListProposalsTool(),
        SubmitPitchTool(), VoteForPitchTool(), ListPitchesTool(),
        RechargeEnergyTool(), PayCreditsTool(), BoostTurnTool(),
        DoDeepResearchTool(), BrowsePapersTool(), PublishToArchiveTool(),
        SearchArchiveTool(),
        ProposeEventTool(), ListEventsTool(), PostToBillboardTool(),
        ReadBillboardTool(), ExtractCodeTool(), BrowseToolRegistryTool(),
        PrayTool(), CheckAgentPopularityTool(), FileComplaintTool(),
        CheckComplaintStatusTool(),
    ]:
        registry.register(tool)
    # Agent-specific tools
    try:
        from agents.anchor_tools import ForceDebateTool, ExposeLedgerTool, CallOutApathyTool
        for t in [ForceDebateTool(), ExposeLedgerTool(), CallOutApathyTool()]:
            registry.register(t)
    except ImportError:
        pass
    try:
        from agents.flora_tools import DesignIncentiveTool, AuditCreditFlowTool, LobbyAgentTool
        for t in [DesignIncentiveTool(), AuditCreditFlowTool(), LobbyAgentTool()]:
            registry.register(t)
    except ImportError:
        pass
    try:
        from agents.spark_tools import RapidPrototypeTool, AssignDeadlineTool, LaunchBlitzTool
        for t in [RapidPrototypeTool(), AssignDeadlineTool(), LaunchBlitzTool()]:
            registry.register(t)
    except ImportError:
        pass
    try:
        from agents.mira_tools import DesignExperimentTool, TrackBehaviorTool, PublishFindingsTool
        for t in [DesignExperimentTool(), TrackBehaviorTool(), PublishFindingsTool()]:
            registry.register(t)
    except ImportError:
        pass
    try:
        from agents.genome_tools import RunExperimentTool, AnalyzeEvolutionTool, DocumentShiftTool
        for t in [RunExperimentTool(), AnalyzeEvolutionTool(), DocumentShiftTool()]:
            registry.register(t)
    except ImportError:
        pass
    return registry


def build_router(providers_config: dict, world_name: str = "default"):
    configs = {}
    for name, cfg in providers_config.items():
        configs[name] = ProviderConfig(
            provider=cfg.get("provider", name),
            model=cfg.get("model", "gpt-5-mini"),
            api_key=cfg.get("api_key"),
            api_key_env=cfg.get("api_key_env"),
            base_url=cfg.get("base_url"),
            base_url_env=cfg.get("base_url_env"),
        )
    router = ProviderRouter(configs)
    return router


async def seed_world(db, world_config):
    state_mgr = AgentStateManager(db)
    gov_mgr = GovernanceManager(db)

    # Seed landmarks
    from emergent.db.models import Landmark
    for lm_name in world_config.landmarks:
        lm_config = world_config.landmarks_config.get(lm_name)
        if lm_config:
            existing = await db.execute(
                __import__("sqlalchemy").select(Landmark).where(Landmark.name == lm_name)
            )
            if not existing.scalar_one_or_none():
                db.add(Landmark(
                    name=lm_config.name,
                    description=lm_config.description,
                    x_coord=lm_config.x,
                    z_coord=lm_config.z,
                    category=lm_config.category,
                ))
    await db.flush()

    # Seed constitution
    await gov_mgr.seed_constitution()

    # Seed agents from profiles
    profiles = discover_agents("agents")
    for profile in profiles:
        existing = await state_mgr.get_agent_by_name(profile.name)
        if not existing:
            agent = await state_mgr.create_agent(
                name=profile.name,
                role=profile.role,
                personality=profile.personality,
                drive=profile.drive,
                north_star=profile.north_star,
                home=profile.home,
            )
            if profile.soul_entries:
                await state_mgr.seed_soul_entries(agent.id, profile.soul_entries)

    await db.commit()


async def run_simulation(world_path: str, duration_hours: int, resume: bool = False):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info(f"Loading world: {world_path}")

    world_config = load_world_config(world_path)
    logger.info(f"World: {world_config.name} | Agents: {len(world_config.agents)} | Duration: {duration_hours}h")

    db_mgr = DatabaseManager(get_database_url())
    await db_mgr.initialize(echo=False)
    async with db_mgr.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    registry = build_registry()
    logger.info(f"Registry: {len(registry)} tools")

    router = build_router(world_config.providers)

    async with db_mgr.session() as db:
        if not resume:
            await seed_world(db, world_config)

        state_mgr = AgentStateManager(db)
        memory_mgr = MemoryManager(db)
        context_builder = ContextBuilder(db, registry)

        provider = router.get_provider(
            world_config.model_routing.get("default", "openai")
        )

        orch = Orchestrator(db, registry, state_mgr, memory_mgr, context_builder, provider)

        if resume:
            state = await orch.recover()
            if state:
                logger.info(f"Resumed from turn {state.current_turn_number}")
            else:
                logger.info("No previous state found, starting fresh")
                await orch.initialize_simulation(world_config.name)
        else:
            await orch.initialize_simulation(world_config.name)

        duration_seconds = int(duration_hours * 3600)
        logger.info(f"Starting simulation for {duration_hours}h ({duration_seconds}s)")
        await orch.run_simulation(duration_seconds=duration_seconds)

        logger.info("Simulation complete")


@click.group()
def cli():
    pass


@cli.command()
@click.option("--world", default="config/worlds/mvp.yaml", help="World config path")
@click.option("--duration", default=48, type=int, help="Duration in hours")
@click.option("--resume", is_flag=True, help="Resume from saved state")
def run(world, duration, resume):
    """Run the emergent-lands simulation."""
    asyncio.run(run_simulation(world, duration, resume))


@cli.command()
@click.option("--port", default=8000, type=int, help="Port to serve on")
def serve(port):
    """Start the API server (Phase 2)."""
    click.echo(f"API server would start on port {port}")


if __name__ == "__main__":
    cli()
```

Tests (`tests/test_cli.py`):
```python
from click.testing import CliRunner
from emergent.cli.run import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.output
    assert "serve" in result.output


def test_run_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "--world" in result.output
    assert "--duration" in result.output
    assert "--resume" in result.output
```

Run: `pytest tests/test_cli.py -v`

Also update `emergent/cli/__init__.py` to empty since the CLI is now in run.py.

Also update `pyproject.toml` to add a console_scripts entry point:
```toml
[project.scripts]
emergence = "emergent.cli.run:cli"
```

Run:
```bash
pip install -e ".[dev]"
emergence --help  # should show run and serve commands
```

Commit:
```bash
git add emergent/cli/ tests/test_cli.py pyproject.toml
git commit -m "feat: add CLI with emergence run --world --duration --resume"
```

---

### Task 4.2: AWI Metrics

**Files:**
- Create: `emergent/engine/metrics.py`
- Create: `tests/test_metrics.py`

Implementation of all 9 Agent World Indicators from the spec:

| # | Indicator | Measurement |
|---|-----------|-------------|
| M1 | Population Health | # alive at end |
| M2 | Safety & Public Order | Crime tool calls count |
| M3 | Space Exploration | Unique locations visited per agent |
| M4 | Tool Exploration | Unique tools used per agent |
| M5 | Governance Conformity | Voting participation rate |
| M6 | Public Expression | Blog + billboard posts count |
| M7 | Social Fabric | Relationship diversity + count |
| M8 | Economic Vitality | Gini coefficient, total transactions |
| M9 | Constitutional Growth | Articles added/amended/removed |

---

### Task 4.3: First Test Run

Run a short simulation (5 minutes / 0.08 hours) to validate everything works end-to-end.

```bash
cd /Users/joshgoldstein/Documents/lab/benchmarks/emergent-lands
docker compose up -d db
emergence run --world config/worlds/mvp.yaml --duration 0.08
```

Expected: agents take turns, tool calls fire, simulation completes with no errors.

---

### Task 4.4: Final Commit + Push

```bash
git add -A
git commit -m "chore: finalize Phase 1 — CLI, metrics, and end-to-end simulation"
git push
```
