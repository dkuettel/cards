from __future__ import annotations

from dataclasses import dataclass, field, replace
from pprint import pprint
from typing import Iterator, Optional
from uuid import uuid4

import requests
from requests.auth import HTTPBasicAuth
from serde import Strict, from_dict, serde, to_dict
from tqdm import tqdm

# TODO things would be cleaner if serde didnt taint the dataclass?
# so we can use it in different places, with different shapes?
# what if I want to use it now also for cache.json?
# of course that's painful if you had to re and re-define renaming and all that


@serde(type_check=Strict)
@dataclass(frozen=True)
class NewCard:
    content: str = field()
    deck_id: str = field(metadata={"serde_rename": "deck-id"})
    review_reverse: bool = field(metadata={"serde_rename": "review-reverse?"})
    # TODO gonna need attachments eventually for pictures


@serde(type_check=Strict)
@dataclass(frozen=True)
class Card:
    id: str = field()
    content: str = field()
    deck_id: str = field(metadata={"serde_rename": "deck-id"})
    review_reverse: bool = field(metadata={"serde_rename": "review-reverse?"})
    # TODO gonna need attachments eventually for pictures

    @staticmethod
    def from_dict(data) -> Card:
        # TODO unfortunately serde doesnt seem to annotate generically for pyright?
        # it does for from_json, maybe I'm importing the wrong thing here?
        # or we dont use the response.json() and the response.text instead?
        # then we have types
        # TODO we have response.text if we want to use generic from_json with pyright
        return from_dict(Card, data)  # pyright: ignore


@serde(type_check=Strict)
@dataclass(frozen=True)
class NewDeck:
    name: str = field()


@serde(type_check=Strict)
@dataclass(frozen=True)
class Deck:
    id: str = field()
    name: str = field()


@dataclass(frozen=True)
class Authentication:
    token: str


def iterate_paged_docs(
    authentication: Authentication, url: str, params: dict
) -> Iterator[dict]:
    limit = 100
    page_params = {"limit": limit}
    auth = HTTPBasicAuth(authentication.token, "")
    while True:
        response = requests.get(url, params={**params, **page_params}, auth=auth)
        assert response.status_code == 200, response.text
        response_json = response.json()
        bookmark = response_json["bookmark"]
        docs = response_json["docs"]
        yield from docs
        # TODO len(docs) < limit would be best
        # but the api doesnt complain if you use a too high limit
        # so len(docs) == 0 is the only robust way I can see, but uses an extra request
        if len(docs) == 0:
            break
        page_params["bookmark"] = bookmark


def list_cards(
    authentication: Authentication, deck_id: Optional[str] = None
) -> list[Card]:
    # TODO where to get the url from? the base url? connection object, includes authentication then?
    url = "https://app.mochi.cards/api/cards/"
    params = {"deck-id": deck_id}
    return [Card.from_dict(d) for d in iterate_paged_docs(authentication, url, params)]


def create_card(authentication: Authentication, new_card: NewCard) -> Card:
    url = "https://app.mochi.cards/api/cards/"
    body = to_dict(new_card)
    auth = HTTPBasicAuth(authentication.token, "")
    response = requests.post(url, json=body, auth=auth)
    assert response.status_code == 200, response.text
    return Card.from_dict(response.json())


def update_card(authentication: Authentication, card: Card) -> Card:
    # TODO not clear in updates, if an entry is missing, it means "leaves as is"?
    # note we do get the full new update card back, so at least we can be sure what's the new state for caching
    url = f"https://app.mochi.cards/api/cards/{card.id}"
    body = to_dict(card)
    body.pop("id")
    auth = HTTPBasicAuth(authentication.token, "")
    response = requests.post(url, json=body, auth=auth)
    assert response.status_code == 200, response.text
    return Card.from_dict(response.json())


def test_list_some():
    deck_id = "-"  # test
    authentication = Authentication("-")
    pprint(list_cards(authentication, deck_id))
    # pprint(len(list_cards(authentication, deck_id)))


def test_add_some():
    deck_id = "-"  # auto
    authentication = Authentication("-")
    count = 20
    # TODO I get about 1.5it/sec, so rate limited, even though it said 5it/sec in the doc? parallel could still help
    # this might even work with threading, right?
    for i in tqdm(range(count)):
        new_card = NewCard(f"({i:03d}) {uuid4()}", deck_id)
        card = create_card(authentication, new_card)
        pprint(card)


def test_update_some():
    deck_id = "-"  # test
    authentication = Authentication("-")
    cards = list_cards(authentication, deck_id)
    card = cards[0]
    pprint(card)
    card = replace(card, content=card.content + f"\nchange {uuid4()}")
    pprint(card)
    card = update_card(authentication, card)
    pprint(card)


if __name__ == "__main__":
    # test_list_some()
    test_add_some()
    # test_update_some()
