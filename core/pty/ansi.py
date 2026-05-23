from __future__ import annotations

import re


ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    """Summarize ANSI escape stripping and return clean text."""

    return ANSI_ESCAPE_RE.sub("", text)
