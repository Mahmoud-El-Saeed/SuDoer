from __future__ import annotations

from enum import Enum


class ModelProvider(str, Enum):
    """Summarize allowed model providers."""

    openai = "openai"
    anthropic = "anthropic"
    ollama = "ollama"
    gemini = "gemini"
    groq = "groq"
