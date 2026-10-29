"""Check the site before committing: links, images, SEO tags, hreflang, JSON-LD, sitemap.

    python scripts/check_site.py

Exits with 1 and lists the problems if anything is wrong. Standard library only.
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent

# Page path -> the path of the same page in the other language.
PAGES = {
    "/": "/de/",
    "/energy-flow-mapper/": "/de/energy-flow-mapper/",
    "/daily-challenge/": "/de/daily-challenge/",
}
PAGES |= {de: en for en, de in list(PAGES.items())}

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title = ""
        self.meta: dict[str, str] = {}
        self.links: list[dict[str, str]] = []
        self.refs: list[str] = []  # local href/src/srcset targets
        self.external_loads: list[str] = []
        self.h1 = 0
        self.ids: set[str] = set()
        self.anchors: list[str] = []
        self.jsonld: list[str] = []
        self.summaries: list[str] = []
        self._in: str | None = None
        self._buf: list[str] = []
        self._summary = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "title":
            self._in, self._buf = "title", []
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key and key not in self.meta:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append(a)
            if a.get("rel") in ("stylesheet", "icon", "apple-touch-icon", "preload"):
                self._ref(a.get("href", ""))
        elif tag == "script":
            if a.get("src"):
                self._ref(a["src"])
            if a.get("type") == "application/ld+json":
                self._in, self._buf = "jsonld", []
        elif tag == "h1":
            self.h1 += 1
        elif tag == "summary":
            self._summary, self._buf = True, []
        if tag == "a" and "href" in a:
            href = a["href"]
            if href.startswith("#"):
                self.anchors.append(href[1:])
            elif href.startswith("/"):
                self.refs.append(href)
        if tag in ("img", "source"):
            for key in ("src", "srcset"):
                for part in a.get(key, "").split(","):
                    url = part.strip().split(" ")[0]
                    if url:
                        self._ref(url)

    def _ref(self, url: str) -> None:
        if url.startswith(("http://", "https://", "//")):
            self.external_loads.append(url)
        elif url:
            self.refs.append(url)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in == "title":
            self.title = "".join(self._buf).strip()
            self._in = None
        elif tag == "script" and self._in == "jsonld":
            self.jsonld.append("".join(self._buf))
            self._in = None
        elif tag == "summary":
            self.summaries.append(" ".join("".join(self._buf).split()))
            self._summary = False

    def handle_data(self, data: str) -> None:
        if self._in or self._summary:
            self._buf.append(data)


def local_file(url_path: str) -> Path:
    path = urlparse(url_path).path
    target = ROOT / path.lstrip("/")
    return target / "index.html" if path.endswith("/") else target


def main() -> int:
    problems: list[str] = []
    origin = None

    for path in sorted(PAGES):
        file = local_file(path)
        if not file.exists():
            problems.append(f"{path}: {file} is missing")
            continue
        text = file.read_text(encoding="utf-8")
        page = Page()
        page.feed(text)

        def bad(msg: str, path: str = path) -> None:
            problems.append(f"{path}: {msg}")

        canonical = next((l["href"] for l in page.links if l.get("rel") == "canonical"), "")
        if origin is None:
            origin = f"https://{urlparse(canonical).netloc}"
        expected = origin + path
        lang = "de" if path.startswith("/de/") else "en"
        en_path = path if lang == "en" else PAGES[path]
        de_path = path if lang == "de" else PAGES[path]

        if page.lang != lang:
            bad(f'html lang is "{page.lang}", expected "{lang}"')
        if canonical != expected:
            bad(f"canonical {canonical} != {expected}")
        alternates = {l.get("hreflang"): l.get("href") for l in page.links if l.get("rel") == "alternate"}
        want = {"en": origin + en_path, "de": origin + de_path, "x-default": origin + en_path}
        if alternates != want:
            bad(f"hreflang links {alternates} != {want}")
        if not 20 <= len(page.title) <= 65:
            bad(f"title has {len(page.title)} characters (20-65): {page.title}")
        description = page.meta.get("description", "")
        if not 70 <= len(description) <= 180:
            bad(f"meta description has {len(description)} characters (70-180)")
        if page.meta.get("og:url") != expected:
            bad("og:url does not match the canonical URL")
        for key in ("og:title", "og:description", "og:image", "og:image:alt", "twitter:card"):
            if not page.meta.get(key):
                bad(f"{key} is missing")
        image = page.meta.get("og:image", "")
        if image.startswith(origin) and not local_file(image[len(origin):]).exists():
            bad(f"og:image {image} does not exist")
        if page.h1 != 1:
            bad(f"{page.h1} h1 elements")
        for ref in page.refs:
            if not local_file(ref).exists():
                bad(f"broken local reference {ref}")
        for anchor in page.anchors:
            if anchor not in page.ids:
                bad(f"broken anchor #{anchor}")
        if page.external_loads:
            bad(f"loads external resources: {page.external_loads}")
        if EMAIL.search(text):
            bad("contains an e-mail address")

        questions: list[str] = []
        for block in page.jsonld:
            try:
                data = json.loads(block)
            except json.JSONDecodeError as err:
                bad(f"JSON-LD does not parse: {err}")
                continue
            for node in data.get("@graph", [data]):
                for value in re.findall(r'https://[^"\s]+', json.dumps(node)):
                    if value.startswith(origin) and "#" not in value:
                        if not local_file(value[len(origin):]).exists():
                            bad(f"JSON-LD URL {value} does not exist")
                if node.get("@type") == "FAQPage":
                    questions = [q["name"] for q in node["mainEntity"]]
        if page.summaries and questions != page.summaries:
            bad("FAQPage JSON-LD questions differ from the FAQ on the page")

    # Sitemap
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(ROOT / "sitemap.xml")
    locs = {loc.text or "" for loc in tree.getroot().findall("s:url/s:loc", ns)}
    want_locs = {f"{origin}{p}" for p in PAGES}
    if locs != want_locs:
        problems.append(f"sitemap.xml: {sorted(locs ^ want_locs)} differ from the pages")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {origin}/sitemap.xml" not in robots:
        problems.append("robots.txt: Sitemap line does not match the site origin")

    if problems:
        print("\n".join(problems))
        return 1
    print(f"OK: {len(PAGES)} pages, origin {origin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
