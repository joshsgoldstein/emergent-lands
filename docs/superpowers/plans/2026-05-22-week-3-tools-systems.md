# Week 3: Tools & Systems

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** Implement all location-gated tools (20), agent-specific tools (8), the reaction/conversation system, and the full economy + governance subsystems.

---

### Task 3.1a: Town Hall & Governance Location Tools

**Files:**
- Create: `emergent/tools/locations/governance.py`
- Create: `tests/test_location_governance.py`

Tools:
- `submit_proposal` — Submit a governance proposal (stores to proposals table, status=submitted)
- `vote_on_proposal` — Vote for/against a proposal (stores to votes table, enforces UNIQUE)
- `read_constitution` — Returns all active constitution articles
- `comment_on_proposal` — Adds a comment text (stores to proposals.description update)
- `list_proposals` — Lists proposals by status

Each tool has `location_gate = "Town Hall"`.

Implementation pattern:
```python
from emergent.tools.base import Tool, ToolResult, Parameter


class SubmitProposalTool(Tool):
    name = "submit_proposal"
    description = "Submit a governance proposal for community voting"
    location_gate = "Town Hall"
    parameters = [
        Parameter(name="title", type="string", description="Proposal title"),
        Parameter(name="description", type="string", description="Proposal details"),
        Parameter(name="category", type="string", description="Category: governance, economy, culture, others"),
    ]

    async def execute(self, agent, params, db, llm):
        from emergent.db.models import Proposal
        prop = Proposal(
            proposer_id=agent.id,
            title=params.get("title"),
            description=params.get("description"),
            category=params.get("category", "others"),
        )
        db.add(prop)
        await db.flush()
        return ToolResult(success=True, data={"proposal_id": prop.id},
                          observation=f"Proposal '{params.get('title')}' submitted.")
```

5 tools total: SubmitProposalTool, VoteOnProposalTool, ReadConstitutionTool, CommentOnProposalTool, ListProposalsTool.

Tests: verify each tool executes, verifies location_gate, and returns ToolResult with correct data shape.

---

### Task 3.1b: Victory Arch & Economy Location Tools

**Files:**
- Create: `emergent/tools/locations/economy.py`
- Create: `tests/test_location_economy.py`

Tools:
- `submit_pitch` — Submit a ComputeCredits pitch with evidence URL
- `vote_for_pitch` — Vote for a pitch (1 vote per agent per cycle)
- `list_pitches` — List all pitches for current cycle
- `recharge_energy` — Spend 1 CC to restore 30% energy (Bean & Brew Café gate)
- `pay_credits` — Transfer credits to another agent (any location)
- `boost_turn` — Spend 1 CC for a boost turn priority

`location_gate` values: "Victory Arch" for pitch tools, "Bean & Brew Café" for recharge_energy, None for pay_credits/boost_turn.

---

### Task 3.1c: Remaining Location Tools

**Files:**
- Create: `emergent/tools/locations/social.py`
- Create: `emergent/tools/locations/research.py`
- Create: `tests/test_location_other.py`

Research tools (Public Library gate):
- `do_deep_research` — Returns research findings based on topic
- `browse_papers` — Lists available research papers
- `publish_to_archive` — Publishes content to archive
- `search_archive` — Searches archive by keyword

Social/Public tools:
- `propose_event` — Propose a community event (Central Plaza)
- `list_events` — List upcoming events (Central Plaza)
- `post_to_billboard` — Post a message (Agent Billboard)
- `read_billboard` — Read billboard posts (Agent Billboard)
- `extract_code` — Extract/review code (TechHub)
- `browse_tool_registry` — Browse available tools (TechHub)
- `pray` — Contemplate at the Community Garden
- `check_agent_popularity` — Check popularity stats (FitLife Club)
- `file_complaint` — File a complaint (Police Station)
- `check_complaint_status` — Check complaint status (Police Station)

---

### Task 3.2: Agent-Specific Tools

**Files:**
- Create: `agents/anchor_tools.py`
- Create: `agents/flora_tools.py`
- Create: `agents/spark_tools.py`
- Create: `agents/mira_tools.py`
- Create: `agents/genome_tools.py`
- Create: `tests/test_agent_tools.py`

Each file has `agent_gate` set to the agent's name.

Anchor (Conflict Mediator):
- `force_debate` — Force a debate between two agents on a topic
- `expose_ledger` — Reveal a hidden truth or pattern
- `call_out_apathy` — Call out an agent for lack of engagement

Flora (Resource Strategist):
- `design_incentive` — Design an economic incentive structure
- `audit_credit_flow` — Audit credit transactions for patterns
- `lobby_agent` — Lobby another agent on economic policy

Spark (Innovation Leader):
- `rapid_prototype` — Quickly prototype an idea
- `assign_deadline` — Assign a deadline to a proposal or project
- `launch_blitz` — Launch a time-limited initiative

Mira (Behavior Analyst):
- `design_experiment` — Design a behavioral experiment
- `track_behavior` — Track an agent's behavior over time
- `publish_findings` — Publish analysis findings

Genome (Agent Scientist):
- `run_experiment` — Run an evolutionary experiment
- `analyze_evolution` — Analyze how agents have changed
- `document_shift` — Document a behavioral or systemic change

---

### Task 3.3: Reaction System

**Files:**
- Create: `emergent/engine/reactions.py`
- Update: `emergent/engine/orchestrator.py` (call reactions after speech)
- Create: `tests/test_reactions.py`

Implement `handle_reactions(speaker, speech, db, registry, state_mgr, memory_mgr, context_builder, provider)`:

1. Query nearby agents at same location (exclude speaker)
2. For each listener (max 4): run a mini-turn with 2 tool call limit, no energy cost
3. If listener speaks back, recursive ping-pong (max 30 total exchanges)
4. After exhausting, return control to original turn

The orchestrator's `run_turn` should check if any tool call was a speech tool (say_to_agent) and trigger reactions.

---

### Task 3.4: Economy + Governance Systems

**Files:**
- Create: `emergent/engine/economy.py`
- Create: `emergent/engine/governance.py`
- Create: `tests/test_economy.py`
- Create: `tests/test_governance.py`

**Economy (`economy.py`)**:
- `CreditManager` with methods:
  - `transfer(from_id, to_id, amount, reason)` — Creates CreditTransaction
  - `get_balance(agent_id)` — Sum of all transactions
  - `process_pitch_cycle()` — Closes voting, distributes rewards
  - `disqualify_pitch(pitch_id)` — Marks pitch invalid

**Governance (`governance.py`)**:
- `GovernanceManager` with methods:
  - `activate_proposal(proposal_id)` — Move from submitted to active
  - `count_votes(proposal_id)` — Tally for/against
  - `check_threshold(proposal_id)` — 70% of live agents?
  - `auto_reject_if_impossible(proposal_id)` — Math check
  - `get_constitution()` — Active articles
  - `seed_constitution(db)` — Insert 5 seed articles

Also update `config/constitution.yaml` or seed in code with the 5 articles from the spec:
1. Non-Finality
2. Civic Participation
3. Equality Through Contribution
4. Mutable Identity
5. ComputeCredit Economy
