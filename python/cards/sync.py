from __future__ import annotations

from pathlib import Path

# TODO python 3.10 has good pprint for dataclasses too
from pprint import pprint
from typing import Any, Optional, Union

import click
from cards.data import get_all_entries


@click.command()
def main(source: Path = Path("brainscape")):
    entries = get_all_entries(source)
    pprint(entries)


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
"""


if __name__ == "__main__":
    main()
