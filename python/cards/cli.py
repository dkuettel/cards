from __future__ import annotations

from typer import Typer

app = Typer()


@app.command()
def sync():
    from cards.config import Config, Credentials
    from cards.sync import sync

    config = Config.from_default_file()
    credentials = Credentials.from_default_file()

    sync(credentials.mochi.token, config.sync.deck_id, config.sync.path)


@app.command()
def preview():
    from cards.config import Config
    from cards.preview import main

    # config = Config.from_default_file()
    config = Config.from_test_file()

    main(config.sync.path)


@app.command()
def test():
    from cards.config import Config, Credentials
    from cards.sync import sync

    config = Config.from_test_file()
    credentials = Credentials.from_default_file()

    sync(credentials.mochi.token, config.sync.deck_id, config.sync.path)
