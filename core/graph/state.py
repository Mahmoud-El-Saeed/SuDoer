from __future__ import annotations

from typing import Optional, TypedDict


class ExecutorState(TypedDict):
    """Summarize executor graph runtime state."""

    goal: str
    plan: list[str]
    current_step: int
    command: str
    pty_output: str
    retry_count: int
    requires_hitl: bool
    validation_reason: Optional[str]
    approved: Optional[bool]
    last_exit_code: Optional[int]
    session_id: Optional[str]
    done: bool
