from pathlib import Path

import click
from tqdm import tqdm

from cards.api import auth_from_token, list_cards
from cards.data import (
    MetaDiff,
    get_cards,
    get_synced_meta,
    read_markdowns,
    read_meta,
    write_meta,
)
from cards.state import MochiDiff, states_from_apply_diff


def sync(token: str, deck_id: str, path: Path):

    auth = auth_from_token(token)

    markdowns = read_markdowns(path)
    meta = read_meta(path)

    synced_meta = get_synced_meta(markdowns, meta)
    meta_diff = MetaDiff.from_states(meta, synced_meta)
    meta_diff.print_summary()
    if meta_diff.count() > 0:
        click.confirm("Continue?", abort=True)
        write_meta(path, synced_meta)
        meta = synced_meta

    existing_cards, new_cards = get_cards(markdowns, meta)

    # TODO do we want to keep state, our best guess of remote?
    # TODO see if we can move all tqdm stuff high up here? so that the decision how/what to show is top-level
    remote = {
        c.id: c
        for c in tqdm(
            list_cards(auth, deck_id),
            total=len(existing_cards),
            desc="list cards",
        )
    }
    for card in remote.values():
        assert not card.archived
        assert not card.trashed
        assert not card.review_reverse
        assert card.template_id is None

    diff = MochiDiff.from_states(remote, existing_cards, new_cards)
    diff.print_summary()

    if diff.count() > 0:
        click.confirm("Continue?", abort=True)
        for state, meta in tqdm(
            states_from_apply_diff(auth, deck_id, remote, diff, meta),
            total=diff.count(),
            desc="sync",
        ):
            # TODO also write state, for cache everytime?
            assert len(state) > 0
            write_meta(path, meta)
