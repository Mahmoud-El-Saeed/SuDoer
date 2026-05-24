from __future__ import annotations

import asyncio
import os
import pty
import re
import select
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from core.pty.ansi import strip_ansi


@dataclass
class PtyOutput:
    """Summarize PTY output chunk."""

    data: str


class PersistentPTY:
    """Summarize a long-lived PTY session."""

    def __init__(self, shell: str = "/bin/bash") -> None:
        """Summarize PTY initialization."""

        self._shell = shell
        self._master_fd: int | None = None
        self._child_pid: int | None = None

    def start(self) -> None:
        """Summarize PTY process startup."""

        if self._master_fd is not None:
            return
        master_fd, slave_fd = pty.openpty()
        pid = os.fork()
        if pid == 0:
            os.setsid()
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            os.close(master_fd)
            os.close(slave_fd)
            os.execv(self._shell, [self._shell])
        os.close(slave_fd)
        self._master_fd = master_fd
        self._child_pid = pid

    def write(self, command: str) -> None:
        """Summarize writing a command to the PTY."""

        if self._master_fd is None:
            raise RuntimeError("PTY not started")
        data = command.rstrip("\n") + "\n"
        os.write(self._master_fd, data.encode())

    async def read_async(self) -> AsyncIterator[PtyOutput]:
        """Summarize async PTY read stream."""

        if self._master_fd is None:
            raise RuntimeError("PTY not started")
        loop = asyncio.get_running_loop()
        master_fd = self._master_fd
        while True:
            ready = await loop.run_in_executor(
                None, lambda: select.select([master_fd], [], [], 0.1)[0]
            )
            if not ready:
                await asyncio.sleep(0)
                continue
            data = os.read(master_fd, 4096)
            if not data:
                break
            text = strip_ansi(data.decode(errors="replace"))
            yield PtyOutput(data=text)

    async def run_command_stream(
        self,
        command: str,
        on_chunk: Callable[[str], Awaitable[None]],
    ) -> int:
        """Summarize running a command and streaming output."""

        if self._master_fd is None:
            raise RuntimeError("PTY not started")
        marker = "__SUDOER_EXIT__:"
        self.write(command)
        self.write(f"echo {marker}$?")
        loop = asyncio.get_running_loop()
        master_fd = self._master_fd
        buffer = ""
        exit_code = 1
        while True:
            ready = await loop.run_in_executor(
                None, lambda: select.select([master_fd], [], [], 0.1)[0]
            )
            if not ready:
                await asyncio.sleep(0)
                continue
            data = os.read(master_fd, 4096)
            if not data:
                break
            text = strip_ansi(data.decode(errors="replace"))
            buffer += text
            marker_index = buffer.find(marker)
            if marker_index != -1:
                before = buffer[:marker_index]
                after = buffer[marker_index + len(marker) :]
                if before:
                    await on_chunk(before)
                match = re.search(r"(\d+)", after)
                if match:
                    exit_code = int(match.group(1))
                    remaining = after[match.end() :]
                    if remaining:
                        await on_chunk(remaining)
                break
            safe_len = max(0, len(buffer) - (len(marker) - 1))
            if safe_len:
                await on_chunk(buffer[:safe_len])
                buffer = buffer[safe_len:]
        if buffer:
            await on_chunk(buffer)
        return exit_code

    def close(self) -> None:
        """Summarize PTY cleanup."""

        if self._master_fd is not None:
            os.close(self._master_fd)
        self._master_fd = None
        self._child_pid = None
