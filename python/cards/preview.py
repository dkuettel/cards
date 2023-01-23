from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Optional

from flask import Flask, current_app, redirect, render_template_string, url_for

app = Flask(__name__)


# NOTE most of <head> is copied from 'pandoc --standalone' to make it work with math
card_template = """
<!doctype html>
<html>
<head>
  <title>preview</title>
  <meta charset="utf-8" />
  <meta name="generator" content="pandoc" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
  <title>test</title>
  <style type="text/css">
      code{white-space: pre-wrap;}
      span.smallcaps{font-variant: small-caps;}
      span.underline{text-decoration: underline;}
      div.column{display: inline-block; vertical-align: top; width: 50%;}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.4/dist/katex.min.js"></script>
  <script>document.addEventListener("DOMContentLoaded", function () {
    var mathElements = document.getElementsByClassName("math");
    for (var i = 0; i < mathElements.length; i++) {
      var texText = mathElements[i].firstChild;
      if (mathElements[i].tagName == "SPAN") { katex.render(texText.data, mathElements[i], { displayMode: mathElements[i].classList.contains("display"), throwOnError: false } );
    }}});</script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.4/dist/katex.min.css" />
</head>
<body>

  preview of {{name}}

  <hr/>

  <div style="width: 25em; font-size: 1.5em">
    {{preview|safe}}
  </div>

  <script>
    setInterval(() => {
      fetch('/mtime')
        .then(response => response.json())
        .then(data => {
          if(data["mtime"]>{{mtime}}) { location.reload(); }
        })
        .catch(error => {
          console.error(error);
        });
    }, 500); // milliseconds
  </script>

</body>
</html>
"""


@app.route("/")
def index():
    return redirect(url_for("preview"))


@app.route("/preview")
def preview():
    # NOTE we read the time _before_ we use it, so worst case it's old, but never new
    path = get_most_recent_md(current_app.config["watch_folder"])
    if path is None:
        return "n/a"
    stat = path.stat()
    try:
        result = run(
            [
                "pandoc",
                str(path),
                "--katex=https://cdn.jsdelivr.net/npm/katex@0.16.4/dist/",
                "--metadata=pagetitle=preview",
                # to find images relative to the markdown file
                f"--resource-path={path.parent}",
                # embeds images, maybe more, but the whole katex js lib is not embedded
                "--self-contained",
                "--to=html",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        return render_template_string(
            card_template,
            preview=result.stdout,
            mtime=stat.st_mtime,
            name=path.relative_to(current_app.config["watch_folder"]),
        )
    except CalledProcessError as e:
        return e.stdout + e.stderr


@app.route("/mtime")
def mtime():
    path = get_most_recent_md(current_app.config["watch_folder"])
    if path is None:
        return {"mtime": -1}
    stat = path.stat()
    return {"mtime": stat.st_mtime}


def get_most_recent_md(folder: Path) -> Optional[Path]:
    candidates = folder.glob("**/*.md")
    candidates = sorted(candidates, key=lambda c: c.stat().st_mtime)
    if len(candidates) == 0:
        return None
    return candidates[-1]


def main(watch_folder: Path = Path("./brainscape")):
    app.config["watch_folder"] = watch_folder
    app.run()
