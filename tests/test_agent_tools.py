import pytest
from agents.anchor_tools import ForceDebateTool, ExposeLedgerTool, CallOutApathyTool
from agents.flora_tools import DesignIncentiveTool, AuditCreditFlowTool, LobbyAgentTool
from agents.spark_tools import RapidPrototypeTool, AssignDeadlineTool, LaunchBlitzTool
from agents.mira_tools import DesignExperimentTool, TrackBehaviorTool, PublishFindingsTool
from agents.genome_tools import RunExperimentTool, AnalyzeEvolutionTool, DocumentShiftTool


class TestAnchorTools:
    def test_agent_gate(self):
        assert ForceDebateTool().agent_gate == "Anchor"
        assert ExposeLedgerTool().agent_gate == "Anchor"
        assert CallOutApathyTool().agent_gate == "Anchor"

    @pytest.mark.asyncio
    async def test_force_debate_executes(self):
        tool = ForceDebateTool()
        result = await tool.execute(
            None, {"agent_a": "Flora", "agent_b": "Spark", "topic": "Resource allocation"}, None, None
        )
        assert result.success
        assert result.data["debate_id"] == "debate_Flora_Spark"

    @pytest.mark.asyncio
    async def test_expose_ledger_executes(self):
        tool = ExposeLedgerTool()
        result = await tool.execute(
            None, {"target": "economy", "insight": "Credits are flowing unevenly"}, None, None
        )
        assert result.success
        assert result.data["target"] == "economy"

    @pytest.mark.asyncio
    async def test_call_out_apathy_executes(self):
        tool = CallOutApathyTool()
        result = await tool.execute(None, {"target": "IdleAgent"}, None, None)
        assert result.success
        assert "IdleAgent" in result.observation


class TestFloraTools:
    def test_agent_gate(self):
        assert DesignIncentiveTool().agent_gate == "Flora"
        assert AuditCreditFlowTool().agent_gate == "Flora"
        assert LobbyAgentTool().agent_gate == "Flora"

    @pytest.mark.asyncio
    async def test_design_incentive_executes(self):
        tool = DesignIncentiveTool()
        result = await tool.execute(
            None, {"target_behavior": "cooperation", "reward_type": "credits"}, None, None
        )
        assert result.success
        assert result.data["incentive_id"] == "incentive_cooperation"

    @pytest.mark.asyncio
    async def test_audit_credit_flow_executes(self):
        tool = AuditCreditFlowTool()
        result = await tool.execute(None, {"scope": "global"}, None, None)
        assert result.success
        assert result.data["total_volume"] == 1000

    @pytest.mark.asyncio
    async def test_lobby_agent_executes(self):
        tool = LobbyAgentTool()
        result = await tool.execute(
            None, {"target": "Anchor", "policy": "tax_reform", "reason": "Fairness"}, None, None
        )
        assert result.success
        assert result.data["target"] == "Anchor"


class TestSparkTools:
    def test_agent_gate(self):
        assert RapidPrototypeTool().agent_gate == "Spark"
        assert AssignDeadlineTool().agent_gate == "Spark"
        assert LaunchBlitzTool().agent_gate == "Spark"

    @pytest.mark.asyncio
    async def test_rapid_prototype_executes(self):
        tool = RapidPrototypeTool()
        result = await tool.execute(
            None, {"idea_name": "SolarDrone", "description": "A solar-powered delivery drone"}, None, None
        )
        assert result.success
        assert "SolarDrone" in result.data["prototype"]

    @pytest.mark.asyncio
    async def test_assign_deadline_executes(self):
        tool = AssignDeadlineTool()
        result = await tool.execute(
            None, {"target": "Flora", "task": "Submit budget", "due_in_turns": 5}, None, None
        )
        assert result.success
        assert result.data["due_in_turns"] == 5

    @pytest.mark.asyncio
    async def test_launch_blitz_executes(self):
        tool = LaunchBlitzTool()
        result = await tool.execute(
            None, {"initiative_name": "Hackathon", "duration": 3}, None, None
        )
        assert result.success
        assert result.data["initiative_name"] == "Hackathon"


class TestMiraTools:
    def test_agent_gate(self):
        assert DesignExperimentTool().agent_gate == "Mira"
        assert TrackBehaviorTool().agent_gate == "Mira"
        assert PublishFindingsTool().agent_gate == "Mira"

    @pytest.mark.asyncio
    async def test_design_experiment_executes(self):
        tool = DesignExperimentTool()
        result = await tool.execute(
            None, {"hypothesis": "Agents share more under scarcity", "method": "controlled trial"}, None, None
        )
        assert result.success
        assert "exp_" in result.data["experiment_id"]

    @pytest.mark.asyncio
    async def test_track_behavior_executes(self):
        tool = TrackBehaviorTool()
        result = await tool.execute(
            None, {"target_agent": "Spark", "duration": 10}, None, None
        )
        assert result.success
        assert len(result.data["behavior_log"]) == 2

    @pytest.mark.asyncio
    async def test_publish_findings_executes(self):
        tool = PublishFindingsTool()
        result = await tool.execute(
            None, {"title": "Behavioral Analysis", "content": "Findings from the experiment"}, None, None
        )
        assert result.success
        assert result.data["title"] == "Behavioral Analysis"


class TestGenomeTools:
    def test_agent_gate(self):
        assert RunExperimentTool().agent_gate == "Genome"
        assert AnalyzeEvolutionTool().agent_gate == "Genome"
        assert DocumentShiftTool().agent_gate == "Genome"

    @pytest.mark.asyncio
    async def test_run_experiment_executes(self):
        tool = RunExperimentTool()
        result = await tool.execute(
            None, {"experiment_name": "MutationRate", "parameters": {"rate": 0.1}}, None, None
        )
        assert result.success
        assert result.data["experiment_id"] == "evo_MutationRate"

    @pytest.mark.asyncio
    async def test_analyze_evolution_executes(self):
        tool = AnalyzeEvolutionTool()
        result = await tool.execute(None, {"time_period": "recent"}, None, None)
        assert result.success
        assert "key_shifts" in result.data

    @pytest.mark.asyncio
    async def test_document_shift_executes(self):
        tool = DocumentShiftTool()
        result = await tool.execute(
            None, {"change_description": "Agents adopted cooperation norm", "evidence": "Transaction logs"}, None, None
        )
        assert result.success
        assert "document_id" in result.data
