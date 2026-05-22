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
