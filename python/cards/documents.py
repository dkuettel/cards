from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from typing import Any, Optional, Type, TypeVar

import pandoc
from beartype.door import die_if_unbearable

T = TypeVar("T")


def if_bearable(value: Any, ty: Type[T]) -> T:
    die_if_unbearable(value, ty)
    return value


@dataclass(frozen=True)
class MetaHeader:
    id: Optional[str]
    reverse_id: Optional[str]

    # TODO would still like to find a better orthogonal serialization lib, with validation

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "reverse-id": self.reverse_id,
            }
        )

    @classmethod
    def from_json(cls, text: str):
        data = json.loads(text)
        return cls(
            id=if_bearable(data.pop("id"), Optional[str]),
            reverse_id=if_bearable(data.pop("reverse-id"), Optional[str]),
        )


@dataclass(frozen=True)
class Document:
    path: Path
    meta: MetaHeader
    md: list
    prompt: Optional[list]
    reverse_md: Optional[list]
    reverse_prompt: Optional[list]

    @classmethod
    def from_path(cls, path: Path):
        meta = read_meta_from_disk(path)
        _, text = split_content(path.read_text())
        return cls.from_text(
            path=path,
            meta=meta,
            text=text,
        )

    @classmethod
    def from_text(cls, path: Path, meta: MetaHeader, text: str):
        from pandoc.types import HorizontalRule, Para, Space, Str  # pyright: ignore

        def is_prompt(e) -> bool:
            return (
                type(e) is Para
                and len(e[0]) >= 2
                and e[0][0] == Str("!")
                and e[0][1] == Space()
            )

        _, body = pandoc.read(text, format="markdown")  # pyright: ignore

        rulers = [i for i, e in enumerate(body) if e == HorizontalRule()]
        assert len(rulers) > 0, body
        pages: list[list] = [
            body[a + 1 : b] for a, b in zip([-1] + rulers, rulers + [len(body)])
        ]
        assert len(pages) >= 2, pages

        md = [e for e in body if not is_prompt(e)]
        prompts = [e for e in pages[0] if is_prompt(e)]
        if len(prompts) == 0:
            prompt = None
        elif len(prompts) == 1:
            prompt = prompts[0][2:]
        else:
            assert False, prompts

        reverse_prompts = [e for e in pages[1] if is_prompt(e)]
        if len(reverse_prompts) == 0:
            reverse_md = None
            reverse_prompt = None
        elif len(reverse_prompts) == 1:
            reverse_md = pages[1] + [HorizontalRule()] + pages[0]
            reverse_md = [e for e in reverse_md if not is_prompt(e)]
            reverse_prompt = reverse_prompts[0][2:]
        else:
            assert False, reverse_prompts

        return cls(
            path=path,
            meta=meta,
            md=md,
            prompt=prompt,
            reverse_md=reverse_md,
            reverse_prompt=reverse_prompt,
        )


def split_content(content: str) -> tuple[Optional[str], str]:
    data = content.split("\n")
    if (
        len(data) >= 4
        and data[0] == "``` {.json}"
        and data[2] == "```"
        and data[3].strip() == ""
    ):
        return data[1], "\n".join(data[4:])
    return None, content


def merge_content(header: Optional[str], text: str) -> str:
    if header is None:
        return text.lstrip("\n")

    assert "\n" not in header
    return "\n".join(
        [
            "``` {.json}",
            header,
            "```",
            "",
        ]
        + text.lstrip("\n").split("\n")
    )


def read_meta_from_disk(path: Path) -> MetaHeader:
    header, _ = split_content(path.read_text())
    if header is None:
        meta = MetaHeader(None, None)
    else:
        meta = MetaHeader.from_json(header)
    return meta


# TODO race conditions could happen here
def write_meta_to_disk(meta: MetaHeader, path: Path):
    _, text = split_content(path.read_text())
    header = meta.to_json()
    assert len(header.split("\n")) == 1, header
    content = merge_content(header, text)
    path.write_text(content)


def get_all_documents(base: Path) -> list[Document]:
    return [Document.from_path(p) for p in base.rglob("*.md")]


def test_meta_injection():
    meta = MetaHeader("first", "second")
    write_meta_to_disk(meta, Path("./example.md"))


def test_loading():
    d = Document.from_path(Path("./example.md"))
    pprint(d)
    print("/////////// forward")
    print(pandoc.write(d.md, format="markdown"))
    if d.reverse_md is not None:
        print("/////////// reverse")
        print(pandoc.write(d.reverse_md, format="markdown"))


if __name__ == "__main__":
    # test_meta_injection()
    test_loading()
