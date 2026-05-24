from __future__ import annotations

import sys

from rich.console import Console

from core.transport.messages import AgentMessage, MessageType


class StreamHandler:
    """Summarize CLI stream splitting behavior."""

    def __init__(self) -> None:
        """Summarize stream handler initialization."""

        self._console = Console(stderr=True)

    def handle(self, message: AgentMessage) -> None:
        """Summarize routing message output to streams."""

        if message.type is MessageType.output:
            output = message.payload.get("output", "")
            if isinstance(output, str):
                sys.stdout.write(output)
                sys.stdout.flush()
            return
        if message.type is MessageType.error:
            detail = message.payload.get("error", "unknown_error")
            self._console.print(f"[bold red]Error:[/bold red] {detail}")
            return
        self._console.print(f"[dim]Event:[/dim] {message.type.value}")

    def prompt_approval(self, prompt: str) -> bool:
        """Summarize user approval prompt handling."""

        self._console.print(f"[yellow]Approval required:[/yellow] {prompt}")
        response = input("Approve? [Y/n]: ").strip().lower()
        if response in {"", "y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        return False
