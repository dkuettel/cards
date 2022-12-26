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
    for row in rows:
        question, answer, name = row
        named = (
            name.replace(" ", "-")
            .replace("/", "-")
            .replace(",", "-")
            .replace(".", "-")
            .replace("?", "")
            .replace(":", "")
            .replace("(", "")
            .replace(")", "")
            .replace('"', "")
            .replace("'", "")
        )
        out = target / (named + ".md")
        assert not out.exists(), out
        out.write_text(name + "\n\n---\n\n" + question + "\n\n---\n\n" + answer)


if __name__ == "__main__":
    cli()
