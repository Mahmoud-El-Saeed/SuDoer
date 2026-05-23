from enum import Enum


class MessageType(str, Enum):
    """Summarize message types exchanged over WebSocket."""

    command = "command"
    output = "output"
    control = "control"
    error = "error"


class ControlAction(str, Enum):
    """Summarize control actions for the transport layer."""

    ping = "ping"
    pong = "pong"
    interrupt = "interrupt"
    resume = "resume"