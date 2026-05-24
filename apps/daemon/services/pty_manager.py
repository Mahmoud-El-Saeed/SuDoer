from __future__ import annotations

import asyncio
import os
import uuid

from core.configs.settings import Settings
from core.graph import build_executor_graph
from core.graph.state import ExecutorState
from core.pty.persistent import PersistentPTY
from core.transport.messages import AgentMessage, MessageType
from core.enums.transport_enums import ControlAction
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


class PtyManager:
    """Summarize daemon PTY manager."""

    def __init__(self) -> None:
        """Summarize PTY manager initialization."""

        self._pty = PersistentPTY()
        self._pty.start()

    def write(self, command: str) -> None:
        """Summarize PTY command dispatch."""

        self._pty.write(command)

    async def submit(
        self,
        command: str,
        outgoing: asyncio.Queue[AgentMessage],
        approval: asyncio.Queue[bool],
    ) -> None:
        """Summarize executing a command via the executor graph."""
        settings = Settings()
        try:
            paths = settings.path_settings()
            await asyncio.to_thread(os.makedirs, paths.data_dir, exist_ok=True)
            async def _request_approval(reason: str) -> bool:
                await outgoing.put(
                    AgentMessage(
                        type=MessageType.control,
                        payload={"action": ControlAction.interrupt, "prompt": reason},
                    )
                )
                return await approval.get()

            async def _emit_output(chunk: str) -> None:
                if chunk:
                    await outgoing.put(
                        AgentMessage(
                            type=MessageType.output,
                            payload={"output": chunk},
                        )
                    )

            graph = build_executor_graph(
                settings,
                self._pty.run_command_stream,
                _request_approval,
                _emit_output,
            )
            initial_state: ExecutorState = {
                "goal": command,
                "plan": [command],
                "current_step": 0,
                "command": "",
                "pty_output": "",
                "retry_count": 0,
                "requires_hitl": False,
                "validation_reason": None,
                "approved": None,
                "last_exit_code": None,
                "session_id": None,
                "done": False,
            }

            thread_id = str(uuid.uuid4())
            async with AsyncSqliteSaver.from_conn_string(paths.sqlite_path) as saver:
                await saver.setup()
                compiled = graph.compile(checkpointer=saver)
                await compiled.ainvoke(
                    initial_state,
                    config={"configurable": {"thread_id": thread_id}},
                )
            await outgoing.put(
                AgentMessage(
                    type=MessageType.control,
                    payload={"action": ControlAction.complete},
                )
            )
        finally:
            self._pty.close()

    def close(self) -> None:
        """Summarize PTY shutdown."""

        self._pty.close()
