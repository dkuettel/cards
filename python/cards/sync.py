from __future__ import annotations

from pathlib import Path

from cards.data.plain.documents import get_all_documents
from cards.data.plain.transform import (
    get_cards_from_documents,
    get_new_cards_from_documents,
)
from cards.mochi.deck import MochiDeck
from cards.mochi.state import MochiDiff, states_from_apply_diff
from tqdm import tqdm

# TODO strange, above isort doesnt seem to understand project and 3rd party imports?

# TODO python 3.10 has good pprint for dataclasses too
# from pprint import pprint

# TODO commited some tokens for testing
# retire token eventually

# TODO changes
# make also removal sync correct
# plus reverse make it so that it says at top, dont use built-in reverse for now
# make it 2 cards: explain & name, with prompt at the top; all my cards should have a prompt, not just vocabs
# how to keep ids when switching card types, is that desired? or just I do it manually?
# and what happens when going from bidi to forward, will it remove the extra id?

# TODO deletion can be dangerous
# maybe archive, or thrash, and also keep a local copy, and also ask user? it should almost never happen anyway


def sync(source: Path):

    token = "-"
    # deck_id = "-"  # brainscape
    deck_id = "-"  # brainscape2
    deck = MochiDeck.from_token(deck_id, token)

    documents = get_all_documents(source)

    new_cards = get_new_cards_from_documents(documents)
    cards = get_cards_from_documents(documents)

    # TODO have this local as well, when/how to rescan to be sure?
    state = {c.id: c for c in deck.list_cards()}
    target = {c.id: c for c in cards}

    diff = MochiDiff.from_targets(state, target, new_cards)
    diff.print_summary()

    if len(diff) > 0:
        for state in tqdm(
            states_from_apply_diff(deck, state, diff), total=len(diff), desc="sync"
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
