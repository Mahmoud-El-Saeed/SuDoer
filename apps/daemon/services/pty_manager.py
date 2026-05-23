from __future__ import annotations

from collections.abc import AsyncIterator

from core.pty.persistent import PersistentPTY, PtyOutput


class PtyManager:
    """Summarize daemon PTY manager."""

    def __init__(self) -> None:
        """Summarize PTY manager initialization."""

        self._pty = PersistentPTY()
        self._pty.start()

    def write(self, command: str) -> None:
        """Summarize PTY command dispatch."""

        self._pty.write(command)

    async def read_stream(self) -> AsyncIterator[PtyOutput]:
        """Summarize PTY output streaming."""

        async for chunk in self._pty.read_async():
            yield chunk

    def close(self) -> None:
        """Summarize PTY shutdown."""

        self._pty.close()
