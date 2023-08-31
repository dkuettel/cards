from __future__ import annotations

import click


@click.group()
def cli():
    pass


@cli.command()
def sync():
    from cards.config import Config, Credentials
    from cards.sync import sync

    config = Config.from_default_file()
    credentials = Credentials.from_default_file()

    sync(credentials.mochi.token, config.sync.deck_id, config.sync.path)


@cli.command()
def preview():
    from cards.config import Config
    from cards.preview import main

    config = Config.from_default_file()

    main(config.sync.path)
