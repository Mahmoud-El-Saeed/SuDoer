from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from core.transport.messages import AgentMessage, MessageType


router = APIRouter()


async def _recv_loop(websocket: WebSocket, outgoing: asyncio.Queue[AgentMessage]) -> None:
    """Summarize inbound message handling and echo placeholder."""

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
            echo = AgentMessage(
                type=MessageType.output,
                session_id=message.session_id,
                payload={"output": f"received: {message.payload}"},
            )
            await outgoing.put(echo)


async def _send_loop(websocket: WebSocket, outgoing: asyncio.Queue[AgentMessage]) -> None:
    """Summarize outbound message loop."""

    while True:
        message = await outgoing.get()
        await websocket.send_text(message.model_dump_json())


@router.websocket("/ws/agent")
async def agent_socket(websocket: WebSocket) -> None:
    """Summarize main bidirectional agent socket."""

    await websocket.accept()
    outgoing: asyncio.Queue[AgentMessage] = asyncio.Queue()  
    send_task = asyncio.create_task(_send_loop(websocket, outgoing))
    recv_task = asyncio.create_task(_recv_loop(websocket, outgoing))
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
