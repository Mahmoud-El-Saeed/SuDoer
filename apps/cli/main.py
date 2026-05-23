from __future__ import annotations

import typer


app = typer.Typer(add_completion=False)


@app.command()
def run() -> None:
    """Summarize CLI entrypoint placeholder."""

    raise SystemExit(0)


if __name__ == "__main__":
    app()
