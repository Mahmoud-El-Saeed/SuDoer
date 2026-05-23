from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from apps.daemon.services.pty_manager import PtyManager
from core.transport.messages import AgentMessage, MessageType


router = APIRouter()


async def _recv_loop(
    websocket: WebSocket,
    outgoing: asyncio.Queue[AgentMessage],
    pty_manager: PtyManager,
) -> None:
    """Summarize inbound message handling."""

    while True:
        data = await websocket.receive_text()
        try:
            message = AgentMessage.model_validate_json(data)
        except ValidationError as exc:
            error = AgentMessage(
                type=MessageType.error,
                payload={"error": "invalid_message", "detail": exc.errors()},
            )
            await outgoing.put(error)
            continue
        if message.type is MessageType.command:
            command = message.payload.get("command")
            if isinstance(command, str) and command.strip():
                pty_manager.write(command)
            else:
                await outgoing.put(
                    AgentMessage(
                        type=MessageType.error,
                        session_id=message.session_id,
                        payload={"error": "missing_command"},
                    )
                )


async def _send_loop(
    websocket: WebSocket,
    outgoing: asyncio.Queue[AgentMessage],
    pty_manager: PtyManager,
) -> None:
    """Summarize outbound message loop."""

    async def _pty_stream() -> None:
        async for chunk in pty_manager.read_stream():
            await outgoing.put(
                AgentMessage(
                    type=MessageType.output,
                    payload={"output": chunk.data},
                )
            )

    stream_task = asyncio.create_task(_pty_stream())
    try:
        while True:
            message = await outgoing.get()
            await websocket.send_text(message.model_dump_json())
    finally:
        stream_task.cancel()
        await asyncio.gather(stream_task, return_exceptions=True)


@router.websocket("/ws/agent")
async def agent_socket(websocket: WebSocket) -> None:
    """Summarize main bidirectional agent socket."""

    await websocket.accept()
    outgoing: asyncio.Queue[AgentMessage] = asyncio.Queue()
    pty_manager = PtyManager()
    send_task = asyncio.create_task(_send_loop(websocket, outgoing, pty_manager))
    recv_task = asyncio.create_task(_recv_loop(websocket, outgoing, pty_manager))
    tasks = {send_task, recv_task}
    try:
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_EXCEPTION,
        )
        for task in done:
            exc = task.exception()
            if exc is not None:
                raise exc
    except WebSocketDisconnect:
        pass
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        pty_manager.close()
