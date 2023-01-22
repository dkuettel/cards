from __future__ import annotations

from dataclasses import dataclass

from cards.mochi.api import ApiCard, create_card, delete_card, list_cards, update_card
from requests.auth import HTTPBasicAuth


@dataclass(frozen=True)
class MochiCard:
    id: str
    content: str
    # TODO eventually we will have attachments, so it makes sense to have a dataclass

    @classmethod
    def from_api_card(cls, card: ApiCard):
        assert card.template_id is None
        assert not card.archived
        assert not card.review_reverse
        return cls(
            card.id,
            card.content,
        )

    def to_api_card(self, deck_id: str) -> ApiCard:
        return ApiCard(
            id=self.id,
            content=self.content,
            deck_id=deck_id,
            template_id=None,
            archived=False,
            review_reverse=False,
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

    def create_card(self, content: str) -> MochiCard:
        api_card = create_card(self.auth, self.deck_id, content)
        return MochiCard.from_api_card(api_card)
