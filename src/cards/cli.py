import subprocess
from pathlib import Path
from typing import Annotated

from typer import Option, Typer


class state:
    base: Path = Path("./data")


app = Typer(pretty_exceptions_enable=True, no_args_is_help=True)


@app.callback()
def main(base: Path):
    state.base = base


@app.command()
def sync():
    from cards.config import Config, Credentials
    from cards.sync import sync

    config = Config.from_base(state.base)
    credentials = Credentials.from_base(state.base)

    sync(credentials.mochi.token, state.base / config.path, config.decks)


@app.command()
def preview():
    from cards.config import Config
    from cards.preview import main

    config = Config.from_base(state.base)

    main(state.base / config.path)


@app.command()
def backup():
    """backup all cards of the configured decks, raw, as json"""
    from cards.backup import backup_deck
    from cards.config import Config, Credentials

    config = Config.from_base(state.base)
    credentials = Credentials.from_base(state.base)

    for deck_name, deck_id in config.decks.items():
        backup_deck(credentials.mochi.token, deck_name, deck_id)


@app.command()
def rename(
    source: Path,
    target: Path,
    edit: Annotated[bool, Option("--edit/--no-edit", "-e")] = False,
):
    # NOTE only renames md files that are also in the meta.json, but not other connected files like images
    from cards.data import rename

    rename(state.base, source, target)

    if edit:
        subprocess.run(["nvim", str(target)], check=True)
