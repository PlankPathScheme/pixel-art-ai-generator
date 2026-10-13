"""CLI entrypoint. Typer app wired to the pipeline runner.

Gotcha: on Windows, typer's default rich console mangles ANSI in cmd.exe
pre-1909. We force legacy_windows=False so users on Win10 1803+ get clean output.
"""
from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from src.pixelgen.config import load_config
from src.pixelgen.pipeline import Pipeline
from src.pixelgen.jobs import Job

app = typer.Typer(
    name="pixelgen",
    help="AI pixel-art generator — prompt or sprite in, pixel sprite out.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console(legacy_windows=False, force_terminal=True)


@app.command()
def generate(
    prompt: str = typer.Option(..., "--prompt", "-p", help="Text prompt for the sprite."),
    reference: Path | None = typer.Option(None, "--ref", "-r", help="Reference sprite to img2img from."),
    out: Path = typer.Option(Path("outputs/sprite.png"), "--out", "-o", help="Output PNG path."),
    config: Path = typer.Option(Path("config/default.yaml"), "--config", "-c"),
    seed: int = typer.Option(-1, "--seed", "-s", help="-1 for random."),
    batch: int = typer.Option(1, "--batch", "-b", min=1, max=64),
) -> None:
    """Run one generation job through the full pipeline."""
    cfg = load_config(config)
    pipe = Pipeline.from_config(cfg)
    job = Job(prompt=prompt, reference=reference, out=out, seed=seed, batch=batch)
    console.print(f"[bold cyan]pixelgen[/] job {job.id} queued — {batch} sprite(s)")
    result = pipe.run(job)
    console.print(f"[bold green]done[/] -> {result.output_path} ({result.elapsed_ms} ms)")


@app.command()
def watch(
    inbox: Path = typer.Option(Path("inbox"), "--inbox", "-i", help="Folder to watch for prompts."),
    outdir: Path = typer.Option(Path("outputs"), "--out", "-o"),
    config: Path = typer.Option(Path("config/default.yaml"), "--config", "-c"),
) -> None:
    """Watch a folder of .txt prompt files and process them as they land."""
    from src.pixelgen.services.watcher import PromptWatcher

    cfg = load_config(config)
    pipe = Pipeline.from_config(cfg)
    watcher = PromptWatcher(inbox=inbox, outdir=outdir, pipeline=pipe, console=console)
    console.print(f"[bold cyan]watching[/] {inbox} -> {outdir}")
    watcher.run_forever()


@app.command()
def info() -> None:
    """Print device, model, and palette info."""
    from src.pixelgen.services.env_probe import probe

    for k, v in probe().items():
        console.print(f"[bold]{k}[/]: {v}")


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("[yellow]interrupted[/]")
        sys.exit(130)