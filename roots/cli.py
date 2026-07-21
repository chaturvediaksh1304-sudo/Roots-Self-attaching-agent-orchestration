"""Roots CLI: init / run / status.

Terminal conventions (Design.md): status colors only (green ok, yellow input,
red failure, dim background), no spinners, real ordered progress lines, no
exclamation points.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from .adapters.base import AdapterError, load_adapter
from .config.project_config import init_project, load_config
from .core import orchestrator
from .memory import store


def _dim(msg: str) -> None:
    click.echo(click.style(msg, dim=True))


def _ok(msg: str) -> None:
    click.echo(click.style(msg, fg="green"))


def _err(msg: str) -> None:
    click.echo(click.style(msg, fg="red"), err=True)


@click.group()
def cli() -> None:
    """Roots - self-attaching agent orchestration."""


@cli.command()
def init() -> None:
    """Scan the project and write .roots/config.yaml."""
    root = Path.cwd()
    config = init_project(root)
    _ok(f"Initialized Roots in {root / '.roots'}")
    _dim(
        f"language={config.language} framework={config.framework} "
        f"backend={config.backend} model={config.model}"
    )
    _dim("Edit .roots/config.yaml to change the model backend.")


def _ask(question: str, index: int, total: int) -> str:
    prompt = click.style(f"Q{index}/{total} {question}", fg="yellow")
    while True:
        answer = click.prompt(prompt, default="", show_default=False)
        if answer.strip():
            return answer.strip()
        _err("Answer cannot be empty. Please respond.")


@cli.command()
@click.option("--goal", default=None, help="The goal (otherwise prompted).")
def run(goal: str | None) -> None:
    """Grill, decompose, dispatch subagents, synthesize a result."""
    root = Path.cwd()
    try:
        config = load_config(root)
    except FileNotFoundError as e:
        _err(str(e))
        raise SystemExit(1)

    if not goal:
        goal = click.prompt(click.style("Goal", fg="yellow"))

    try:
        adapter = load_adapter(config.backend, model=config.model)
    except (ValueError, TypeError) as e:
        _err(f"could not build backend '{config.backend}': {e}")
        raise SystemExit(1)

    try:
        result = asyncio.run(
            orchestrator.run(goal, root, adapter, _ask, on_progress=_dim)
        )
    except AdapterError as e:
        _err(f"model backend error: {e}")
        raise SystemExit(1)

    failed = [o for o in result.outcomes if o.status != "ok"]
    if failed:
        _err(f"{len(failed)} subagent(s) failed - see {result.result_path}")
    _ok(f"Result: {result.result_path}")
    _dim(f"Memory: {result.memory_path}")
    _dim(f"History: {result.history_path}")


@cli.command()
def status() -> None:
    """Print the current run's memory."""
    root = Path.cwd()
    try:
        click.echo(store.read_memory(root))
    except FileNotFoundError as e:
        _err(str(e))
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
