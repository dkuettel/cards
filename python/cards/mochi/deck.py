from __future__ import annotations

from dataclasses import dataclass

from requests.auth import HTTPBasicAuth

from cards.mochi.api import (
    Attachment,
    Card,
    create_card,
    delete_card,
    list_cards,
    update_card,
)


# TODO should we go from data sources directly to Api-like card?
# not sure, this makes it an easy layer focusing only on what we use?
# TODO currently we use this as == and sync decision? so it has to be a stable thing, we can reference files for example, need final bytes
@dataclass(frozen=True)
class MochiCard:
    id: str
    content: str
    attachments: list[Attachment]

    @classmethod
    def from_api_card(cls, card: Card):
        return cls(
            card.id,
            card.content,
            card.attachments,  # TODO mutability?
        )

    def to_api_card(self, deck_id: str) -> Card:
        return Card(
            id=self.id,
            content=self.content,
            deck_id=deck_id,
            attachments=self.attachments,  # TODO mutability?
        )


@dataclass
class MochiDeck:
    deck_id: str
    auth: HTTPBasicAuth

    @classmethod
    def from_token(cls, deck_id: str, token: str):
        return cls(
            deck_id,
            HTTPBasicAuth(token, ""),
        )

    def list_cards(self) -> list[MochiCard]:
        api_cards = list_cards(self.auth, self.deck_id)
        return [MochiCard.from_api_card(c) for c in api_cards]

    def delete_card(self, card_id: str):
        delete_card(self.auth, card_id)

    def update_card(self, card: MochiCard) -> MochiCard:
        api_card = update_card(self.auth, card.to_api_card(self.deck_id))
        return MochiCard.from_api_card(api_card)

    def create_card(self, content: str, attachments: list[Attachment]) -> MochiCard:
        api_card = create_card(self.auth, self.deck_id, content, attachments)
        return MochiCard.from_api_card(api_card)
