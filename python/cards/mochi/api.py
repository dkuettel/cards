from __future__ import annotations

from base64 import b64encode
from pathlib import Path
from pprint import pprint
from typing import Iterator, Literal
from uuid import uuid4

import requests
from pydantic import BaseModel, ConfigDict, Field
from requests.auth import HTTPBasicAuth
from tqdm import tqdm


def url_at(at: str) -> str:
    return f"https://app.mochi.cards/api/{at}"


def model_config():
    return ConfigDict(
        alias_generator=lambda x: x.replace("_", "-"),
        strict=True,
    )


def to_post_body(m: Card | Attachment) -> dict:
    return m.model_dump(by_alias=True)


# TODO is there a better way to do it?
# a subclass pollutes the namespace
# and makes certain things impossible when it clashes with pydantic's own model_* methods ...
# like clean dataclasses and an external function for load/save?
class Attachment(BaseModel):
    model_config = model_config()

    file_name: str
    content_type: str
    data: str

    @classmethod
    def from_bytes(cls, file_name: str, content_type: str, data: bytes):
        return cls(
            file_name=file_name,
            content_type=content_type,
            data=b64encode(data).decode("utf-8"),
        )

    @classmethod
    def from_file(cls, file_name: str, path: Path):
        match path.suffix:
            case ".png":
                content_type = "image/png"
            case ".jpg" | ".jpeg":
                content_type = "image/jpeg"
            case _:
                assert False, path
        return cls.from_bytes(
            file_name,
            content_type,
            path.read_bytes(),
        )


class Card(BaseModel):
    model_config = model_config()

    id: str
    content: str
    deck_id: str
    attachments: list[Attachment] = Field(default_factory=list)
    # TODO does pydantic understand that? aliases cannot be based on type I guess :/
    # otherwise we load them and validate separately, probably better, here we just want to mirror the api
    archived: Literal[False] = Field(default=False, alias="archived?")
    trashed: Literal[False] = Field(default=False, alias="trashed?")
    review_reverse: Literal[False] = Field(default=False, alias="review-reverse?")
    template_id: Literal[None] = None


def iterate_paged_docs(auth: HTTPBasicAuth, url: str, params: dict) -> Iterator[dict]:
    limit = 100
    page_params = {"limit": limit}
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


def raw_list_cards(auth: HTTPBasicAuth, deck_id: None | str = None) -> list[dict]:
    url = url_at("cards")
    params = {}
    if deck_id is not None:
        params["deck-id"] = deck_id
    return [
        doc for doc in tqdm(iterate_paged_docs(auth, url, params), desc="list cards")
    ]


def list_cards(auth: HTTPBasicAuth, deck_id: None | str = None) -> list[Card]:
    return [Card(**doc) for doc in raw_list_cards(auth, deck_id)]


def create_card(
    auth: HTTPBasicAuth, deck_id: str, content: str, attachments: list[Attachment]
) -> Card:
    url = url_at("cards")
    body = {
        "deck-id": deck_id,
        "content": content,
        "attachments": [to_post_body(i) for i in attachments],
    }
    response = requests.post(url, json=body, auth=auth)
    assert response.status_code == 200, response.text
    return Card(**response.json())


def get_card(auth: HTTPBasicAuth, card_id: str) -> Card:
    url = url_at(f"cards/{card_id}")
    response = requests.get(url, auth=auth)
    assert response.status_code == 200, response.text
    return Card(**response.json())


def update_card(auth: HTTPBasicAuth, card: Card) -> Card:
    url = url_at(f"cards/{card.id}")
    body = to_post_body(card)
    response = requests.post(url, json=body, auth=auth)
    assert response.status_code == 200, response.text
    return Card(**response.json())


def delete_card(auth: HTTPBasicAuth, card_id: str):
    url = url_at(f"cards/{card_id}")
    response = requests.delete(url, auth=auth)
    assert response.status_code == 200, response.text


def test_list_some(auth: HTTPBasicAuth, deck_id: str):
    pprint(list_cards(auth, deck_id))


def test_add_some(auth: HTTPBasicAuth, deck_id: str):
    count = 20
    # TODO I get about 1.5it/sec, so rate limited, even though it said 5it/sec in the doc? parallel could still help
    # this might even work with threading, right?
    for i in tqdm(range(count)):
        c = create_card(auth, deck_id, f"({i:03d}) {uuid4()}", [])
        pprint(c)


def test_update_some(auth: HTTPBasicAuth, deck_id: str):
    cards = list_cards(auth, deck_id)
    card = cards[0]
    pprint(card)
    card.content = card.content + f"\nchange {uuid4()}"
    pprint(card)
    card = update_card(auth, card)
    pprint(card)


def test_retrieve_card(
    auth: HTTPBasicAuth, deck_id: str = "7PK828fj", card_id: str = "Z5qXONkU"
):

    url = url_at(f"cards/{card_id}")
    response = requests.get(url, auth=auth)
    print(response.json())

    url = url_at("cards")
    params = {}
    params["deck-id"] = deck_id
    [card] = [
        doc
        for doc in tqdm(iterate_paged_docs(auth, url, params), desc="list cards")
        if doc["id"] == card_id
    ]
    print(card)

def auth_from_token(token: str) -> HTTPBasicAuth:
    return HTTPBasicAuth(token, "")


if __name__ == "__main__":
    from cards.config import Credentials

    credentials = Credentials.from_default_file()
    auth = HTTPBasicAuth(credentials.mochi.token, "")
    deck_id = "-"
    # test_list_some(auth, deck_id)
    # test_add_some(auth, deck_id)
    # test_update_some(auth, deck_id)
    test_retrieve_card(auth)
