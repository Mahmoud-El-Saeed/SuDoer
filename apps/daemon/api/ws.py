from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from apps.daemon.services.pty_manager import PtyManager
from core.enums.transport_enums import ControlAction
from core.transport.messages import AgentMessage, MessageType


router = APIRouter()


async def _recv_loop(
    websocket: WebSocket,
    outgoing: asyncio.Queue[AgentMessage],
    pty_manager: PtyManager,
    approval: asyncio.Queue[bool],
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
                asyncio.create_task(pty_manager.submit(command, outgoing, approval))
            else:
                await outgoing.put(
                    AgentMessage(
                        type=MessageType.error,
                        session_id=message.session_id,
                        payload={"error": "missing_command"},
                    )
                )
        elif message.type is MessageType.control:
            action = message.payload.get("action")
            approved = message.payload.get("approved")
            if isinstance(action, str):
                try:
                    action_value = ControlAction(action)
                except ValueError:
                    continue
            elif isinstance(action, ControlAction):
                action_value = action
            else:
                continue
            if action_value is ControlAction.resume and isinstance(approved, bool):
                await approval.put(approved)


async def _send_loop(
    websocket: WebSocket,
    outgoing: asyncio.Queue[AgentMessage],
    pty_manager: PtyManager,
) -> None:
    """Summarize outbound message loop."""

    while True:
        message = await outgoing.get()
        await websocket.send_text(message.model_dump_json())


@router.websocket("/ws/agent")
async def agent_socket(websocket: WebSocket) -> None:
    """Summarize main bidirectional agent socket."""

    await websocket.accept()
    outgoing: asyncio.Queue[AgentMessage] = asyncio.Queue()
    approval: asyncio.Queue[bool] = asyncio.Queue()
    pty_manager = PtyManager()
    send_task = asyncio.create_task(_send_loop(websocket, outgoing, pty_manager))
    recv_task = asyncio.create_task(_recv_loop(websocket, outgoing, pty_manager, approval))
    tasks = {send_task, recv_task}
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    except WebSocketDisconnect:
        pass
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        pty_manager.close()
        if websocket.client_state.name == "CONNECTED":
            await websocket.close()
