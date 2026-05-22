import os
import pytest
from emergent.models.router import ProviderRouter, ProviderConfig


def test_router_empty_config():
    router = ProviderRouter(configs={})
    with pytest.raises(ValueError, match="No provider configured"):
        router.get_provider("default")


def test_router_default_provider():
    configs = {
        "default": ProviderConfig(
            provider="openai",
            model="gpt-5-mini",
            api_key="sk-test",
        ),
    }
    router = ProviderRouter(configs)
    provider = router.get_provider("default")
    assert provider.name == "openai"
    assert provider.model_id == "gpt-5-mini"


def test_router_env_key_override(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
    configs = {
        "openai": ProviderConfig(
            provider="openai",
            model="gpt-5-mini",
            api_key_env="OPENAI_API_KEY",
        ),
    }
    router = ProviderRouter(configs)
    assert router._resolve_api_key(configs["openai"]) == "sk-from-env"


def test_router_unknown_provider_type():
    configs = {
        "default": ProviderConfig(
            provider="nonexistent", model="gpt-5-mini", api_key="sk-test"
        ),
    }
    router = ProviderRouter(configs)
    with pytest.raises(ValueError, match="Unknown provider type"):
        router.get_provider("default")


def test_router_caches_providers():
    configs = {
        "default": ProviderConfig(
            provider="openai", model="gpt-5-mini", api_key="sk-test"
        ),
    }
    router = ProviderRouter(configs)
    p1 = router.get_provider("default")
    p2 = router.get_provider("default")
    assert p1 is p2
