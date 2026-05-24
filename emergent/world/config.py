import os
from dataclasses import dataclass, field
from typing import Optional, Union

import yaml


@dataclass
class LandmarkConfig:
    name: str
    description: str = ""
    x: float = 0.0
    z: float = 0.0
    category: str = "public"
    tools: list[str] = field(default_factory=list)


@dataclass
class AgentConfig:
    name: str
    provider: Optional[str] = None
    model: Optional[str] = None


@dataclass
class WorldConfig:
    name: str
    duration_hours: int = 48
    timezone: str = "America/New_York"
    real_time_scale: float = 1.0
    model_routing: dict = field(default_factory=lambda: {"default": "openai", "overrides": {}})
    providers: dict = field(default_factory=dict)
    agents: list[Union[str, AgentConfig]] = field(default_factory=list)
    landmarks: list[str] = field(default_factory=list)
    landmarks_config: dict[str, LandmarkConfig] = field(default_factory=dict)
    spawn: dict[str, str] = field(default_factory=dict)

    def agent_configs_dict(self) -> dict[str, AgentConfig]:
        result = {}
        for entry in self.agents:
            if isinstance(entry, AgentConfig):
                result[entry.name] = entry
        return result


def load_landmark_config(path: str) -> LandmarkConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return LandmarkConfig(
        name=data["name"],
        description=data.get("description", ""),
        x=float(data.get("x", 0)),
        z=float(data.get("z", 0)),
        category=data.get("category", "public"),
        tools=data.get("tools", []),
    )


def load_world_config(
    world_path: str,
    landmark_dir: Optional[str] = None,
) -> WorldConfig:
    if not os.path.exists(world_path):
        raise FileNotFoundError(f"World config not found: {world_path}")

    with open(world_path) as f:
        data = yaml.safe_load(f)

    if landmark_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(world_path)))
        landmark_dir = os.path.join(base_dir, "landmarks")

    landmarks_config: dict[str, LandmarkConfig] = {}
    if os.path.isdir(landmark_dir):
        for fname in os.listdir(landmark_dir):
            if fname.endswith(".yaml"):
                try:
                    lc = load_landmark_config(os.path.join(landmark_dir, fname))
                    landmarks_config[lc.name] = lc
                except Exception:
                    pass

    raw_agents = data.get("agents", [])
    parsed_agents = []
    for entry in raw_agents:
        if isinstance(entry, dict):
            parsed_agents.append(AgentConfig(**entry))
        else:
            parsed_agents.append(entry)

    return WorldConfig(
        name=data["name"],
        duration_hours=data.get("duration_hours", 48),
        timezone=data.get("timezone", "America/New_York"),
        real_time_scale=data.get("real_time_scale", 1.0),
        model_routing=data.get("model_routing", {"default": "openai", "overrides": {}}),
        providers=data.get("providers", {}),
        agents=parsed_agents,
        landmarks=data.get("landmarks", []),
        landmarks_config=landmarks_config,
        spawn=data.get("spawn", {}),
    )
