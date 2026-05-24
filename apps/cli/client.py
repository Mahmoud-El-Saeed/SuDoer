from __future__ import annotations


from collections.abc import AsyncIterator
from typing import Optional

import websockets

from core.transport.messages import AgentMessage, MessageType


class CliWebSocketClient:
    """Summarize CLI WebSocket client."""

    def __init__(self, url: str) -> None:
        """Summarize client initialization."""

        self._url = url
        self._connection: Optional[websockets.ClientProtocol] = None

    async def __aenter__(self) -> "CliWebSocketClient":
        """Summarize connecting to the daemon socket."""

        self._connection = await websockets.connect(self._url)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Summarize closing the daemon socket."""

        if self._connection is not None:
            await self._connection.close()

    async def send_command(self, command: str) -> None:
        """Summarize sending a command message."""

        if self._connection is None:
            raise RuntimeError("WebSocket connection not established")
        message = AgentMessage(
            type=MessageType.command,
            payload={"command": command},
        )
        await self._connection.send(message.model_dump_json())

    async def receive(self) -> AsyncIterator[AgentMessage]:
        """Summarize receiving messages from the daemon."""

        if self._connection is None:
            raise RuntimeError("WebSocket connection not established")
        async for raw in self._connection:
            yield AgentMessage.model_validate_json(raw)
