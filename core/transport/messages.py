from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from core.enums.transport_enums import MessageType, ControlAction


class AgentMessage(BaseModel):
    """Summarize WebSocket message payload."""

    type: MessageType
    session_id: Optional[str] = Field(default=None)
    payload: dict[str, Any] = Field(default_factory=dict)


class CommandPayload(BaseModel):
    """Summarize command payload schema."""

    command: str


class OutputPayload(BaseModel):
    """Summarize output payload schema."""

    output: str
    is_error: bool = False


class ControlPayload(BaseModel):
    """Summarize control payload schema."""

    action: ControlAction