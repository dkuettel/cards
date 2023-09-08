from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from typing import Iterator, Optional
from uuid import uuid4

import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm

from cards.tools import if_bearable


def url_at(at: str) -> str:
    return f"https://app.mochi.cards/api/{at}"


@dataclass(frozen=True)
class ApiAttachment:
    file_name: str
    content_type: str
    data: str

    @classmethod
    def from_bytes(cls, file_name: str, content_type: str, data: bytes):
        return cls(
            file_name,
            content_type,
            b64encode(data).decode("utf-8"),
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

    @classmethod
    def from_doc(cls, doc: dict):
        return cls(
            file_name=if_bearable(doc["file-name"], str),
            content_type=if_bearable(doc["content-type"], str),
            data=if_bearable(doc["data"], str),
        )

    def to_post_body(self) -> dict:
        return {
            "file-name": self.file_name,
            "content-type": self.content_type,
            "data": self.data,
        }


@dataclass(frozen=True)
class ApiCard:
    id: str
    content: str
    deck_id: str
    attachments: list[ApiAttachment]

    @classmethod
    def from_doc(cls, doc: dict):
        # TODO we dont support any cards with this (unused, and/or sync problems)
        assert not doc.get("archived?", False)
        assert not doc.get("trashed?", False)
        assert not doc.get("review-reverse?", False)
        assert doc.get("template-id", None) is None
        # TODO try this other serialization/validation lib that is meant for this use-case?
        id = if_bearable(doc.get("id"), str)
        content = if_bearable(doc.get("content"), str)
        deck_id = if_bearable(doc.get("deck-id"), str)
        attachments = [
            ApiAttachment.from_doc(i)
            for i in if_bearable(doc.get("attachments", []), list)
        ]
        return cls(id, content, deck_id, attachments)

    def to_post_body(self) -> dict:
        # TODO not clear in updates, if an entry is missing, it means "leave as is"?
        # note we do get the full new update card back, so at least we can be sure what's the new state for caching
        return {
            "content": self.content,
            "deck-id": self.deck_id,
            "attachments": [i.to_post_body() for i in self.attachments],
        }

    def with_content(self, content: str) -> ApiCard:
        return ApiCard(
            self.id,
            content,
            self.deck_id,
            self.attachments,
        )


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


def list_cards(auth: HTTPBasicAuth, deck_id: Optional[str] = None) -> list[ApiCard]:
    url = url_at("cards")
    params = {}
    if deck_id is not None:
        params["deck-id"] = deck_id
    return [
        ApiCard.from_doc(doc)
        for doc in tqdm(iterate_paged_docs(auth, url, params), desc="list cards")
    ]


def create_card(
    auth: HTTPBasicAuth, deck_id: str, content: str, attachments: list[ApiAttachment]
) -> ApiCard:
    url = url_at("cards")
    body = {
        "deck-id": deck_id,
        "content": content,
        "attachments": [i.to_post_body() for i in attachments],
    }
    response = requests.post(url, json=body, auth=auth)
    assert response.status_code == 200, response.text
    return ApiCard.from_doc(response.json())


def get_card(auth: HTTPBasicAuth, card_id: str) -> ApiCard:
    url = url_at(f"cards/{card_id}")
    response = requests.get(url, auth=auth)
    assert response.status_code == 200, response.text
    return ApiCard.from_doc(response.json())


def update_card(auth: HTTPBasicAuth, card: ApiCard) -> ApiCard:
    url = url_at(f"cards/{card.id}")
    body = card.to_post_body()
    response = requests.post(url, json=body, auth=auth)
    assert response.status_code == 200, response.text
    return ApiCard.from_doc(response.json())


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
    card = card.with_content(card.content + f"\nchange {uuid4()}")
    pprint(card)
    card = update_card(auth, card)
    pprint(card)


if __name__ == "__main__":
    from cards.config import Credentials

    credentials = Credentials.from_default_file()
    auth = HTTPBasicAuth(credentials.mochi.token, "")
    deck_id = "-"  # api-test
    test_list_some(auth, deck_id)
    # test_add_some(auth, deck_id)
    # test_update_some(auth, deck_id)
