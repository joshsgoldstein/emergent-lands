import os
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class AgentProfile:
    name: str
    role: str
    personality: str
    drive: str
    north_star: str
    soul_entries: list[str] = field(default_factory=list)
    home: Optional[str] = None
    tools: list[str] = field(default_factory=list)


def load_agent_profile(path: str) -> AgentProfile:
    with open(path) as f:
        data = yaml.safe_load(f)
    return AgentProfile(
        name=data["name"],
        role=data.get("role", ""),
        personality=data.get("personality", ""),
        drive=data.get("drive", ""),
        north_star=data.get("north_star", ""),
        soul_entries=data.get("soul_entries", []),
        home=data.get("home"),
        tools=data.get("tools", []),
    )


def discover_agents(agent_dir: str = "agents") -> list[AgentProfile]:
    profiles = []
    if not os.path.isdir(agent_dir):
        return profiles
    for fname in sorted(os.listdir(agent_dir)):
        if fname.endswith(".yaml"):
            profiles.append(load_agent_profile(os.path.join(agent_dir, fname)))
    return profiles
