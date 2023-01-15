from __future__ import annotations

from pathlib import Path

import click
from cards.data import get_all_entries
from cards.documents import get_all_documents
from cards.entries import get_cards_from_entries
from tqdm import tqdm

from cards import entries as E, mochi as M
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


@click.command()
def main(source: Path = Path("brainscape/v2")):

    authentication = M.Authentication("55a09ced245dd6fde6780896")
    # deck_id = "VetSe1ij"  # brainscape
    deck_id = "f1Xj0eiR"  # brainscape2

    documents = get_all_documents(source)

    new_cards = get_new_cards(documents)
    print(f"{len(new_cards)} new cards to add.")
    for new_card in tqdm(new_cards, desc="add new cards"):
        nc = new_card_from_new_card(new_card, deck_id)
        c = M.create_card(authentication, nc)
        new_card.update_on_disk(c.id)

    cards = get_cards(documents)
    print(f"{len(cards)} to potentially update.")
    # changed = 0
    for card in tqdm(cards, desc="update cards"):
        c = card_from_card(card, deck_id)
        u = M.update_card(authentication, c)
        # TODO ok that was stupid, of course this is always the same
        # we would have to check _before_ ...
        # if u != c:
        #     changed += 1
    # print(f"{changed}/{len(cards)} actual changes.")


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


""" draft
we want a representation of mochi state
and a way to send it
diff it
store it
validate it

but we can start with just a state
and a full sender (idempotent)
gives us full functionality already
rest is just speed

the state needs to mirror what we care about on mochi
so first need to understand that

but the fact that we transform entries into multiple cards is separate

note there is also an "update at" field for cards
would that be enough to know when there is a change?
but still requires a full listing anyway

even just the fact that we need a deck for the content
and we need the id, means we need to query, or have local data
"""

""" minimal version
load all entries
transform them to cards (Card or NewCard)
and send all updates
also sync back (for NewCard) the ids

transform is the main thing left right now
entries.py that knows how to take Entry and make (New)Card?
and sync back ids to mochi.json?

now what's left is there an easy way to transform between very similar dataclasses?
i'm fine with manual writing, but I want to be informed if something is missing
so I should stop having default values? does pyright understand =field if no default value?
if I want some defaults, I should only make new and from and other classmethods to never fall into this trap
(trap: new mochi property, but defaulted, and it's never passed, even though both side have it)
"""

# TODO how to use pyright globally as a linter
# does lsp does it, globally, not just per file?
# or add it somehow as a linter instead?

if __name__ == "__main__":
    main()
