from __future__ import annotations

from pathlib import Path

import click
from tqdm import tqdm

from cards.data import get_all_documents
from cards.mochi.deck import MochiDeck
from cards.mochi.state import MochiDiff, states_from_apply_diff


def sync(token: str, deck_id: str, path: Path):

    deck = MochiDeck.from_token(deck_id, token)

    documents = get_all_documents(path)
    for d in tqdm(documents, desc="sync local meta"):
        d.sync_local_meta()

    cards = [
        c
        for d in tqdm(documents, desc="documents to cards")
        for c in d.get_mochi_cards()
    ]

    # TODO do we want to keep state, our best guess of remote?
    # TODO we could have a guess for the count, and the a better tqdm, should we make things with yield, so that we do tqdm high up only?
    state = deck.list_cards()
    diff = MochiDiff.from_states(state, cards)
    diff.print_summary()

    if diff.count() > 0:
        click.confirm("Continue?", abort=True)
        for state in tqdm(
            states_from_apply_diff(deck, state, diff), total=diff.count(), desc="sync"
        ):
            # TODO should write state to file everytime
            pass
