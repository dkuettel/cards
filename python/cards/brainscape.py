import csv
from pathlib import Path

import click


@click.group()
def cli():
    pass


@cli.command()
def transform(
    export_path=Path("brainscape/export-2022-12-26.csv"), target=Path("brainscape")
):
    rows = export_path.read_text().splitlines()
    rows = list(csv.reader(rows))[1:]
    for i, (question, answer, name) in enumerate(rows):
        out = target / f"todo-{i:03d}/card.md"
        assert not out.exists(), out
        out.parent.mkdir()
        out.write_text(name + "\n\n---\n\n" + question + "\n\n---\n\n" + answer)


if __name__ == "__main__":
    cli()
