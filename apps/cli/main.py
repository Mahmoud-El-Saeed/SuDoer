from __future__ import annotations

import asyncio

import typer

from apps.cli.client import CliWebSocketClient
from apps.cli.stream_handler import StreamHandler


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
                stream_handler.handle(message)

    asyncio.run(_run())


if __name__ == "__main__":
    app()
