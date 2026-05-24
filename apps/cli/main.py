from __future__ import annotations

import asyncio

import typer

from apps.cli.client import CliWebSocketClient
from apps.cli.stream_handler import StreamHandler
from core.enums.transport_enums import ControlAction
from core.transport.messages import MessageType


app = typer.Typer(add_completion=False)


@app.command()
def run(
    command: str = typer.Argument(..., help="Command to execute"),
    url: str = typer.Option(
        "ws://localhost:8000/ws/agent", help="Daemon WebSocket URL"
    ),
) -> None:
    """Summarize CLI run command."""

    async def _run() -> None:
        stream_handler = StreamHandler()
        async with CliWebSocketClient(url) as client:
            await client.send_command(command)
            async for message in client.receive():
                if message.type is MessageType.control:
                    action = message.payload.get("action")
                    if isinstance(action, str):
                        try:
                            action_value = ControlAction(action)
                        except ValueError:
                            action_value = None
                    elif isinstance(action, ControlAction):
                        action_value = action
                    else:
                        action_value = None
                    if action_value is ControlAction.interrupt:
                        prompt = message.payload.get("prompt", "Proceed?")
                        if not isinstance(prompt, str):
                            prompt = "Proceed?"
                        approved = stream_handler.prompt_approval(prompt)
                        await client.send_control(ControlAction.resume, approved=approved)
                        continue
                    if action_value is ControlAction.complete:
                        break
                stream_handler.handle(message)

    asyncio.run(_run())


if __name__ == "__main__":
    app()
