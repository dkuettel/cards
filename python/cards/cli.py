from __future__ import annotations

from pathlib import Path

import click


@click.group()
def cli():
    pass


@cli.command()
def sync():
    from cards.sync import sync

    sync(Path("brainscape/v2"))
