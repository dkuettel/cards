from __future__ import annotations

from pathlib import Path

import click
from cards.documents import get_all_documents
from tqdm import tqdm

from cards import mochi as M
from cards.cards import Card, NewCard, get_cards, get_new_cards

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


# TODO eventually move it all to a cli file
@click.command()
def main(source: Path = Path("brainscape/v2")):

    authentication = M.Authentication("55a09ced245dd6fde6780896")
    # deck_id = "VetSe1ij"  # brainscape
    deck_id = "f1Xj0eiR"  # brainscape2

    documents = get_all_documents(source)
    m_cards = M.list_cards(authentication, deck_id)

    new_cards = get_new_cards(documents)
    print(f"{len(new_cards)} new cards to add.")
    for new_card in tqdm(new_cards, desc="add new cards"):
        nc = new_card_from_new_card(new_card, deck_id)
        c = M.create_card(authentication, nc)
        new_card.update_on_disk(c.id)

    # TODO cache yes, but also missing deletion, so need to get full list anyway
    # and probably want to move the doc meta update (when prompt disappears) to documents?
    # and explicitly call it, just like we update disk here explicity on NewCard

    cards = get_cards(documents)
    print(f"{len(cards)} to potentially update.")
    for card in tqdm(cards, desc="update cards"):
        c = card_from_card(card, deck_id)
        M.update_card(authentication, c)
    # TODO not giving a stats now for how much actually changed
    # print(f"{changed}/{len(cards)} actual changes.")

    known_ids = {i for doc in documents for i in doc.meta.ids()}
    mochi_ids = {i.id for i in m_cards}
    # TODO here could also double check both directions if ids match up
    ids_to_delete = mochi_ids - known_ids
    print(f"{len(ids_to_delete)} cards to delete on mochi.")
    for card_id in tqdm(ids_to_delete, desc="delete cards"):
        # TODO there is also an option to set trash to True
        # is it then not listed anymore in this deck? I think it's listed
        # so manual stuff will be listed, since we dont parse the trashed yet
        # that's a bit inconsistent
        M.delete_card(authentication, card_id)


def card_from_card(card: Card, deck_id: str) -> M.Card:
    return M.Card(
        id=card.id,
        content=card.content,
        deck_id=deck_id,
        review_reverse=False,
    )


def new_card_from_new_card(new_card: NewCard, deck_id: str) -> M.NewCard:
    return M.NewCard(
        content=new_card.content,
        deck_id=deck_id,
        review_reverse=False,
    )


# TODO how to use pyright globally as a linter
# does lsp does it, globally, not just per file?
# or add it somehow as a linter instead?

if __name__ == "__main__":
    main()
