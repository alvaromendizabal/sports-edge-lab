"""Export only reviewed public assets for a browser-viewable static host.

No provider data, models, owner packages, secrets or runtime inference. Hosting
and repository commits remain distinct operations with separate receipts.
"""
from __future__ import annotations

import argparse
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re

from .build import EVIDENCE, ROOT, render


REPOSITORY = "https://github.com/alvaromendizabal/sports-edge-lab"
ASSETS = {"index.html", "october-29.html", "monitor.js", "evidence.json", "hosting-provenance.json"}


def repository_links(content: str, *, source_ref: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", source_ref):
        raise ValueError("an exact public source commit is required")

    def convert(match):
        value = match.group(1)
        if value.startswith("#") or value.startswith(("https://", "mailto:")):
            return match.group(0)
        if value == "index.html":
            return 'href="october-29.html"'
        if value == "monitor.html":
            return 'href="index.html"'
        target = posixpath.normpath(posixpath.join("docs/nba", value))
        if target.startswith("../") or target.startswith("/") or "\\" in target:
            raise ValueError("public link escaped the repository")
        return f'href="{escape(REPOSITORY + "/blob/" + source_ref + "/" + target, quote=True)}"'

    return re.sub(r'href="([^"]+)"', convert, content)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.scripts = [], []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "script":
            self.scripts.append(attrs.get("src"))


def bundle(*, source_ref: str) -> dict[str, str]:
    data = json.loads(EVIDENCE.read_text())
    monitor = repository_links(render(data), source_ref=source_ref)
    october = repository_links((ROOT / "docs/nba/index.html").read_text(), source_ref=source_ref)
    assets = {"index.html": monitor, "october-29.html": october,
              "monitor.js": (ROOT / "docs/nba/monitor.js").read_text(),
              "evidence.json": json.dumps(data, ensure_ascii=False, indent=2) + "\n",
              "hosting-provenance.json": json.dumps({
                  "schema": "public.nba.static-projection.v1", "repository": REPOSITORY,
                  "source_commit": source_ref, "assets": sorted(ASSETS),
                  "scope": "Reviewed public aggregates and invented examples only",
                  "live_provider_requests": 0, "private_runtime_artifacts": False,
                  "deployment_status": "DEFINED_BY_HOST_RECEIPT_NOT_THIS_FILE",
              }, indent=2) + "\n"}
    for filename in ("index.html", "october-29.html"):
        parser = Links()
        parser.feed(assets[filename])
        for href in parser.links:
            if not (href.startswith(("#", "https://", "mailto:")) or href in ASSETS):
                raise ValueError("unresolved static-host navigation: " + href)
        if any(src != "monitor.js" for src in parser.scripts):
            raise ValueError("unreviewed script dependency")
    return assets


def export(destination: Path, *, source_ref: str) -> dict:
    destination = destination.resolve()
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("static export requires a new or empty destination")
    assets = bundle(source_ref=source_ref)
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in assets.items():
        (destination / name).write_text(content)
    return {"status": "EXPORTED_NOT_DEPLOYED", "files": sorted(assets),
            "public_source_commit": source_ref, "provider_requests": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--source-ref", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(export(args.destination, source_ref=args.source_ref), indent=2))


if __name__ == "__main__":
    main()
