from pathlib import Path

import click
from tqdm import tqdm

from cards.data import (
    MetaDiff,
    get_cards,
    get_synced_meta,
    read_markdowns,
    read_meta,
    write_meta,
)
from cards.mochi.deck import MochiDeck
from cards.mochi.state import MochiDiff, states_from_apply_diff


def sync(token: str, deck_id: str, path: Path):

    deck = MochiDeck.from_token(deck_id, token)

    markdowns = read_markdowns(path)
    meta = read_meta(path)

    synced_meta = get_synced_meta(markdowns, meta)
    meta_diff = MetaDiff.from_states(meta, synced_meta)
    meta_diff.print_summary()
    if meta_diff.count() > 0:
        click.confirm("Continue?", abort=True)
        write_meta(path, synced_meta)
        meta = synced_meta

    # TODO do we want to keep state, our best guess of remote?
    # TODO we could have a guess for the count, and the a better tqdm, should we make things with yield, so that we do tqdm high up only?
    remote = {c.id: c for c in deck.list_cards()}
    existing_cards, new_cards = get_cards(markdowns, meta)

    diff = MochiDiff.from_states(remote, existing_cards, new_cards)
    diff.print_summary()

    if diff.count() > 0:
        click.confirm("Continue?", abort=True)
        for state, meta in tqdm(
            states_from_apply_diff(deck, remote, diff, meta),
            total=diff.count(),
            desc="sync",
        ):
            # TODO also write state, for cache everytime?
            assert len(state) > 0
            write_meta(path, meta)
