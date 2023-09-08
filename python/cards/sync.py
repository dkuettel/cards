from __future__ import annotations

from pathlib import Path

import click
from tqdm import tqdm

from cards.data.rich.documents import get_all_rich_documents
from cards.mochi.deck import MochiDeck
from cards.mochi.state import MochiDiff, states_from_apply_diff


def sync(token: str, deck_id: str, path: Path):

    deck = MochiDeck.from_token(deck_id, token)

    # documents = get_all_documents(path)
    documents = get_all_rich_documents(path)
    # documents = align_and_write_metas_to_disk(documents)

    cards = [c for d in documents for c in d.get_mochi_cards()]

    # new_cards = get_new_cards_from_documents(documents)
    # target_cards = get_cards_from_documents(documents)
    # existing_cards, new_cards = split_cards(cards)
    # TODO should we even split? if MochiDiff could do it instead?

    # TODO have this local as well, when/how to rescan to be sure?
    # state = {c.id: c for c in deck.list_cards()}
    # target = {c.get_card().id: c for c in target_cards}

    # diff = MochiDiff.from_targets(state, target, new_cards)
    # TODO or do we want to keep state, our best guess of remote?
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

    # TODO cache yes, but also missing deletion, so need to get full list anyway
    # and probably want to move the doc meta update (when prompt disappears) to documents?
    # and explicitly call it, just like we update disk here explicity on NewCard

    # TODO wasnt there also a field trashed? need to deal with it


# TODO how to use pyright globally as a linter
# does lsp does it, globally, not just per file?
# or add it somehow as a linter instead?
