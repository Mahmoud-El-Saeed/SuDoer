from __future__ import annotations

import re
from dataclasses import dataclass

from core.configs.settings import Settings
from core.enums.model_provider import ModelProvider
from core.factories.models import build_llm_class


@dataclass(frozen=True)
class ValidationResult:
    """Summarize validator decision details."""

    is_safe: bool
    reason: str


DESTRUCTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\brm\s+-rf\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bdd\s+if=\b"),
    re.compile(r"\bchmod\s+0?0?0\b"),
    re.compile(r"\bchown\s+.*\s+/"),
    re.compile(r"\bshutdown\b|\breboot\b"),
)


def regex_validate(command: str) -> ValidationResult:
    """Summarize regex-based destructive detection."""

    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return ValidationResult(False, "Potentially destructive command")
    return ValidationResult(True, "No destructive pattern matched")


def llm_validate(goal: str, command: str, settings: Settings) -> ValidationResult:
    """Summarize LLM-based intent validation."""

    llm_settings = settings.validator_llm_settings()
    if llm_settings.api_key is None and llm_settings.provider in {
        ModelProvider.openai,
        ModelProvider.anthropic,
        ModelProvider.gemini,
        ModelProvider.groq,
    }:
        return ValidationResult(True, "LLM validation skipped (missing API key)")
    llm_class = build_llm_class(llm_settings)
    llm = llm_class(
        model=llm_settings.name,
        api_key=llm_settings.api_key,
        base_url=llm_settings.base_url,
        temperature=0,
    )
    prompt = (
        "You are a command safety validator. "
        "Answer SAFE or UNSAFE, then a short reason.\n"
        f"Goal: {goal}\n"
        f"Command: {command}\n"
    )
    try:
        response = llm.invoke(prompt)
    except Exception as exc:  # noqa: BLE001
        return ValidationResult(True, f"LLM validation skipped ({exc})")
    content = getattr(response, "content", str(response)).strip()
    normalized = content.lower()
    if normalized.startswith("safe"):
        return ValidationResult(True, content)
    if normalized.startswith("unsafe"):
        return ValidationResult(False, content)
    return ValidationResult(False, "Validator returned unclear verdict")


def validate_command(goal: str, command: str, settings: Settings) -> ValidationResult:
    """Summarize combined regex + LLM validation."""

    regex_result = regex_validate(command)
    if not regex_result.is_safe:
        return regex_result
    return llm_validate(goal, command, settings)
