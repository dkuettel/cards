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


@app.command()
def convert():
    import json
    from pathlib import Path

    from cards.data.markdown import Meta, write_meta

    source = Path("data/rich")
    target = Path("data/markdown")
    target.mkdir(parents=True, exist_ok=True)

    metas = {}

    for path in source.glob("*/content.md"):
        meta = json.loads((path.parent / "meta.json").read_text())
        name = path.parent.name
        target_path = target / f"{name}.md"
        metas[target_path.absolute().relative_to(target.absolute())] = Meta(
            meta["forward"], meta["backward"]
        )
        target_path.write_text(path.read_text())

    write_meta(target, metas)
