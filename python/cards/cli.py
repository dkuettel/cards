from __future__ import annotations

from dataclasses import dataclass

from typer import Typer


@dataclass
class State:
    test: bool = False


state = State()

app = Typer()


@app.callback()
def main(test: bool = False):
    state.test = test


@app.command()
def sync():
    from cards.config import Config, Credentials
    from cards.sync import sync

    config = Config.from_test_flag(state.test)
    credentials = Credentials.from_default_file()

    sync(credentials.mochi.token, config.sync.deck_id, config.sync.path)


@app.command()
def preview():
    from cards.config import Config
    from cards.preview import main

    config = Config.from_test_flag(state.test)

    main(config.sync.path)
