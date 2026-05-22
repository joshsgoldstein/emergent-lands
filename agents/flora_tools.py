from emergent.tools.base import Tool, ToolResult, Parameter


class DesignIncentiveTool(Tool):
    name = "design_incentive"
    description = "Design an economic incentive structure"
    agent_gate = "Flora"
    parameters = [
        Parameter(name="target_behavior", type="string", description="The behavior to incentivize"),
        Parameter(name="reward_type", type="string", description="Type of reward (credits, recognition, priority)"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "target_behavior": params.get("target_behavior"),
                "reward_type": params.get("reward_type"),
                "incentive_id": f"incentive_{params.get('target_behavior')}",
            },
            observation=f"Incentive designed: reward {params.get('reward_type')} for {params.get('target_behavior')}",
        )


class AuditCreditFlowTool(Tool):
    name = "audit_credit_flow"
    description = "Audit credit transactions for patterns"
    agent_gate = "Flora"
    parameters = [
        Parameter(name="scope", type="string", description="Scope of the audit (global, sector, agent)"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "scope": params.get("scope"),
                "total_volume": 1000,
                "transaction_count": 42,
                "top_flows": [{"from": "Anchor", "to": "Mira", "amount": 200}],
            },
            observation=f"Credit audit complete for scope: {params.get('scope')}",
        )


class LobbyAgentTool(Tool):
    name = "lobby_agent"
    description = "Lobby another agent on economic policy"
    agent_gate = "Flora"
    parameters = [
        Parameter(name="target", type="string", description="Agent to lobby"),
        Parameter(name="policy", type="string", description="The policy to advocate for"),
        Parameter(name="reason", type="string", description="Why the agent should support this policy"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "target": params.get("target"),
                "policy": params.get("policy"),
                "reason": params.get("reason"),
            },
            observation=f"Flora lobbies {params.get('target')} on policy '{params.get('policy')}'",
        )
