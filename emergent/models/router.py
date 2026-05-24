import os
from dataclasses import dataclass
from typing import Optional

from emergent.models.base import LLMProvider
from emergent.models.openai_provider import OpenAIProvider


@dataclass
class ProviderConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    base_url_env: Optional[str] = None


class ProviderRouter:
    def __init__(self, configs: dict[str, ProviderConfig]):
        self._configs = configs
        self._providers: dict[str, LLMProvider] = {}

    def _resolve_api_key(self, config: ProviderConfig) -> str:
        if config.api_key_env:
            key = os.getenv(config.api_key_env)
            if key:
                return key
        if config.api_key:
            return config.api_key
        raise ValueError(
            f"No API key for provider '{config.provider}'. "
            f"Set {config.api_key_env} env var or provide api_key."
        )

    def _resolve_base_url(self, config: ProviderConfig) -> Optional[str]:
        if config.base_url_env:
            return os.getenv(config.base_url_env, config.base_url)
        return config.base_url

    def _build_provider(self, name: str, config: ProviderConfig) -> LLMProvider:
        api_key = self._resolve_api_key(config)
        base_url = self._resolve_base_url(config)
        if config.provider == "openai":
            return OpenAIProvider(
                api_key=api_key,
                model=config.model,
                base_url=base_url,
            )
        raise ValueError(f"Unknown provider type: {config.provider}")

    def get_provider(self, name: str = "default", model: Optional[str] = None) -> LLMProvider:
        cache_key = f"{name}:{model}" if model else name
        if model is None and cache_key in self._providers:
            return self._providers[cache_key]
        if name not in self._configs:
            raise ValueError(f"No provider configured for '{name}'")
        config = self._configs[name]
        if model:
            config = ProviderConfig(
                provider=config.provider,
                model=model,
                api_key=config.api_key,
                api_key_env=config.api_key_env,
                base_url=config.base_url,
                base_url_env=config.base_url_env,
            )
        provider = self._build_provider(name, config)
        self._providers[cache_key] = provider
        return provider
