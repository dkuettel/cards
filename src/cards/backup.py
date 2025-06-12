import datetime
import json
from pathlib import Path

import click
from tqdm import tqdm

from cards.api import auth_from_token, raw_list_cards


def backup_deck(token: str, deck_id: str):
    date = datetime.date.today()
    path = Path(f"backup-mochi-deck-{deck_id}-from-{date.isoformat()}.json")
    if path.exists():
        click.confirm(f"Overwrite {path}?", abort=True)

    auth = auth_from_token(token)
    cards = list(tqdm(raw_list_cards(auth, deck_id), desc="list cards"))

    path.write_text(json.dumps(cards, indent=4))
