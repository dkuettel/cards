from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path

from PIL import Image
from serde import serde
from serde.json import from_json, to_json
from tqdm import tqdm

from cards.api import Attachment
from cards.markdown import Direction, Markdown


# TODO same name as api.Card ... can we have a better name here?
@dataclass
class Card:
    content: str
    attachments: list[Attachment]
    path: Path
    direction: Direction


@serde
class Meta:
    forward: None | str
    backward: None | str

    def set_by_direction(self, direction: Direction, value: None | str):
        match direction:
            case Direction.forward:
                self.forward = value
            case Direction.backward:
                self.backward = value
            case _:
                assert False

    def get_by_direction(self, direction: Direction) -> None | str:
        match direction:
            case Direction.forward:
                return self.forward
            case Direction.backward:
                return self.backward
            case _:
                assert False


def read_markdowns(base: Path) -> dict[Path, Markdown]:
    base = base.absolute()
    paths = list(base.rglob("*.md"))
    return {
        path.relative_to(base): Markdown.from_path(path)
        for path in tqdm(paths, desc="read markdowns")
    }


def read_meta(base: Path) -> dict[Path, Meta]:
    at = base / "meta.json"
    if not at.exists():
        return {}
    meta_str = from_json(dict[Path, Meta], at.read_text())
    meta = {Path(p): m for p, m in meta_str.items()}
    return meta


# TODO we could work with absolute paths outside this boundary instead
# and only convert when saving and loading?
def write_meta(base: Path, meta: dict[Path, Meta]):
    meta_str = {str(p): m for p, m in meta.items()}
    (base / "meta.json").write_text(to_json(meta_str, indent=4))


def get_synced_meta(
    markdowns: dict[Path, Markdown], meta: dict[Path, Meta]
) -> dict[Path, Meta]:
    def f(path: Path, markdown: Markdown) -> Meta:
        if path not in meta:
            return Meta(None, None)
        return Meta(
            forward=meta[path].forward,
            backward=meta[path].backward if markdown.has_reverse_prompt() else None,
        )

    return {
        path: f(path, markdown)
        for path, markdown in tqdm(markdowns.items(), desc="sync local meta")
    }


def as_flat_meta_state(state: dict[Path, Meta]) -> set[tuple[Path, Direction, str]]:
    return {
        (path, direction, id)
        for path, meta in state.items()
        for direction in Direction
        if (id := meta.get_by_direction(direction)) is not None
    }


@dataclass
class MetaDiff:
    changes: list[tuple[Path, Direction, str | None, str | None]]

    @classmethod
    def from_states(cls, state: dict[Path, Meta], target: dict[Path, Meta]):
        changes = []
        for path in set(state) | set(target):
            for direction in Direction:
                now = state.get(path, Meta(None, None)).get_by_direction(direction)
                then = target.get(path, Meta(None, None)).get_by_direction(direction)
                if now != then:
                    changes.append((path, direction, now, then))
        return cls(changes)

    def print_summary(self):
        for path, direction, now, then in self.changes:
            print(f"{path} {direction.value} {now} -> {then}")

    def count(self) -> int:
        return len(self.changes)


def get_cards(
    base: Path, markdowns: dict[Path, Markdown], meta: dict[Path, Meta]
) -> tuple[dict[str, Card], list[Card]]:
    existing_cards = dict()
    new_cards = []
    for path, markdown in tqdm(markdowns.items(), desc="make cards"):
        # TODO it's not very clear when we have relative paths and when absolute paths
        # we could always work with absolute paths unless in the name?
        # need to see how that handles well with meta.json and other stuff
        images = Images.from_base(base / path.parent)
        markdown = markdown.with_rewritten_images(images.collect)
        card = Card(
            markdown.maybe_prompted().as_mochi_md_str(),
            images.as_api_attachments(),
            path,
            Direction.forward,
        )
        if meta.get(path, Meta(None, None)).forward is None:
            new_cards.append(card)
        else:
            # TODO any checking for duplicate ids?
            existing_cards[meta[path].forward] = card
        if markdown.has_reverse_prompt():
            card = Card(
                markdown.reversed().maybe_prompted().as_mochi_md_str(),
                images.as_api_attachments(),
                path,
                Direction.backward,
            )
            if meta.get(path, Meta(None, None)).backward is None:
                new_cards.append(card)
            else:
                # TODO any checking for duplicate ids?
                existing_cards[meta[path].backward] = card
    return existing_cards, new_cards


@dataclass
class Images:
    base: Path
    next_index: int
    data: dict[str, bytes]
    max_width: int = 800

    @classmethod
    def from_base(cls, base: Path):
        return cls(base, 0, {})

    def collect(self, path: str) -> tuple[str, str]:
        local = self.base / path
        # TODO mochis requirements on names here a bit arbitrary, and not correctly documented too
        name = f"i{self.next_index:08}.png"
        remote = f"@media/{name}"
        self.next_index += 1

        with Image.open(local) as image:
            if image.width > self.max_width:
                height = round(image.height * self.max_width / image.width)
                image = image.resize((self.max_width, height))
            data = BytesIO()
            image.save(data, "png")
            self.data[name] = data.getvalue()

        hash = sha256()
        hash.update(self.data[name])

        return remote, hash.hexdigest()

    def as_api_attachments(self) -> list[Attachment]:
        return [
            Attachment.from_bytes(name, "image/png", data)
            for name, data in self.data.items()
        ]
