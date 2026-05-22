import os
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
    assert "Town Hall" in config.landmarks


def test_load_world_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_world_config("/nonexistent/world.yaml")


def test_load_world_config_no_landmark_dir(tmp_path):
    world_file = tmp_path / "world.yaml"
    world_file.write_text(SAMPLE_WORLD_YAML)
    config = load_world_config(str(world_file))
    assert config.name == "Test World"
    assert config.landmarks_config == {}
