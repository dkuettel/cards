"""
implement relevant parts of
https://mochi.cards/docs/api/
"""

from __future__ import annotations

from base64 import b64encode
from pathlib import Path
from typing import Iterator

import requests
from pydantic import BaseModel, ConfigDict, Field
from requests.auth import HTTPBasicAuth


def url_at(at: str) -> str:
    return f"https://app.mochi.cards/api/{at}"


def model_config():
    return ConfigDict(
        alias_generator=lambda x: x.replace("_", "-"),
        strict=True,
    )


def body_from_model(m: BaseModel) -> dict:
    return m.model_dump(by_alias=True)


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
    archived: bool = Field(default=False, alias="archived?")
    trashed: bool = Field(default=False, alias="trashed?")
    review_reverse: bool = Field(default=False, alias="review-reverse?")
    template_id: None | str = None


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


def raw_list_cards(auth: HTTPBasicAuth, deck_id: None | str = None) -> Iterator[dict]:
    url = url_at("cards")
    params = {}
    if deck_id is not None:
        params["deck-id"] = deck_id
    # TODO now deal with tqdm higher up, where we might have some len() estimate
    return iterate_paged_docs(auth, url, params)


def list_cards(auth: HTTPBasicAuth, deck_id: None | str = None) -> Iterator[Card]:
    for doc in raw_list_cards(auth, deck_id):
        yield Card(**doc)


def raw_create_card(
    auth: HTTPBasicAuth, deck_id: str, content: str, attachments: list[Attachment]
) -> dict:
    url = url_at("cards")
    body = {
        "deck-id": deck_id,
        "content": content,
        "attachments": [body_from_model(i) for i in attachments],
    }
    response = requests.post(url, json=body, auth=auth)
    assert response.status_code == 200, response.text
    return response.json()


def create_card(
    auth: HTTPBasicAuth, deck_id: str, content: str, attachments: list[Attachment]
) -> Card:
    return Card(**raw_create_card(auth, deck_id, content, attachments))


def raw_retrieve_card(auth: HTTPBasicAuth, card_id: str) -> dict:
    url = url_at(f"cards/{card_id}")
    response = requests.get(url, auth=auth)
    assert response.status_code == 200, response.text
    return response.json()


def retrieve_card(auth: HTTPBasicAuth, card_id: str) -> Card:
    return Card(**raw_retrieve_card(auth, card_id))


def raw_update_card(auth: HTTPBasicAuth, card: dict) -> dict:
    url = url_at(f"cards/{card['id']}")
    response = requests.post(url, json=card, auth=auth)
    assert response.status_code == 200, response.text
    return response.json()


def update_card(auth: HTTPBasicAuth, card: Card) -> Card:
    return Card(**raw_update_card(auth, body_from_model(card)))


def delete_card(auth: HTTPBasicAuth, card_id: str):
    url = url_at(f"cards/{card_id}")
    response = requests.delete(url, auth=auth)
    assert response.status_code == 200, response.text


def auth_from_token(token: str) -> HTTPBasicAuth:
    return HTTPBasicAuth(token, "")
