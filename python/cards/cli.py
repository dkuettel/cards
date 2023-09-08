from pathlib import Path

from typer import Typer


class state:
    base: Path = Path("./data")


app = Typer()


@app.callback()
def main(test: bool = False):
    if test:
        state.base = Path("./test-data")


@app.command()
def sync():
    from cards.config import Config, Credentials
    from cards.sync import sync

    config = Config.from_base(state.base)
    credentials = Credentials.from_base(state.base)

    sync(credentials.mochi.token, config.sync.deck_id, state.base / config.sync.path)


@app.command()
def preview():
    from cards.config import Config
    from cards.preview import main

    config = Config.from_base(state.base)

    main(state.base / config.sync.path)


@app.command()
def backup():
    """backup all cards of the default deck, raw, as json"""
    from cards.backup import backup_deck
    from cards.config import Config, Credentials

    config = Config.from_base(state.base)
    credentials = Credentials.from_base(state.base)

    backup_deck(credentials.mochi.token, config.sync.deck_id)
