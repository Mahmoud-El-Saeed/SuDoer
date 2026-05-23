from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from typing import Any, TypeVar

from core.enums.model_provider import ModelProvider
from core.configs.settings import EmbeddingSettings, LlmSettings


TModel = TypeVar("TModel")


@dataclass(frozen=True)
class ProviderSpec:
    """Summarize provider import requirements."""

    provider: ModelProvider
    import_path: str
    package_name: str
    llm_class_name: str
    embedding_class_name: str


class ProviderRegistryError(RuntimeError):
    """Summarize provider registry validation errors."""


def _build_registry() -> dict[ModelProvider, ProviderSpec]:
    """Summarize provider registry initialization."""

    return {
        ModelProvider.openai: ProviderSpec(
            provider=ModelProvider.openai,
            import_path="langchain_openai",
            package_name="langchain-openai",
            llm_class_name="ChatOpenAI",
            embedding_class_name="OpenAIEmbeddings",
        ),
        ModelProvider.anthropic: ProviderSpec(
            provider=ModelProvider.anthropic,
            import_path="langchain_anthropic",
            package_name="langchain-anthropic",
            llm_class_name="ChatAnthropic",
            embedding_class_name="",
        ),
        ModelProvider.ollama: ProviderSpec(
            provider=ModelProvider.ollama,
            import_path="langchain_ollama",
            package_name="langchain-ollama",
            llm_class_name="ChatOllama",
            embedding_class_name="OllamaEmbeddings",
        ),
        ModelProvider.gemini: ProviderSpec(
            provider=ModelProvider.gemini,
            import_path="langchain_google_genai",
            package_name="langchain-google-genai",
            llm_class_name="ChatGoogleGenerativeAI",
            embedding_class_name="GoogleGenerativeAIEmbeddings",
        ),
        ModelProvider.groq: ProviderSpec(
            provider=ModelProvider.groq,
            import_path="langchain_groq",
            package_name="langchain-groq",
            llm_class_name="ChatGroq",
            embedding_class_name="",
        ),
    }


REGISTRY: dict[ModelProvider, ProviderSpec] = _build_registry()


def _require_provider(provider: ModelProvider) -> ProviderSpec:
    """Summarize provider validation and dependency checks."""

    spec = REGISTRY.get(provider)
    if spec is None:
        raise ProviderRegistryError(
            f"Provider '{provider}' is not allowed by registry."
        )
    try:
        import_module(spec.import_path)
    except ModuleNotFoundError as exc:
        raise ProviderRegistryError(
            f"Provider '{provider}' requires '{spec.package_name}'. "
            f"Install it to continue."
        ) from exc
    return spec


def _provider_guard(provider: ModelProvider, build: Callable[[ProviderSpec], TModel]) -> TModel:
    """Summarize provider validation before model creation."""

    spec = _require_provider(provider)
    return build(spec)


def build_llm_class(settings: LlmSettings) -> type[Any]:
    """Summarize LLM factory validation and class resolution."""

    def _build(spec: ProviderSpec) -> type[Any]:
        module = import_module(spec.import_path)
        if not spec.llm_class_name:
            raise ProviderRegistryError(
                f"Provider '{spec.provider}' does not define an LLM class."
            )
        return getattr(module, spec.llm_class_name)

    return _provider_guard(settings.provider, _build)


def build_embedding_class(settings: EmbeddingSettings) -> type[Any]:
    """Summarize embedding factory validation and class resolution."""

    def _build(spec: ProviderSpec) -> type[Any]:
        module = import_module(spec.import_path)
        if not spec.embedding_class_name:
            raise ProviderRegistryError(
                f"Provider '{spec.provider}' does not define embeddings."
            )
        return getattr(module, spec.embedding_class_name)

    return _provider_guard(settings.provider, _build)
