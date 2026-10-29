"""Switch the site to a custom domain (or back to skylolerr.github.io).

Every absolute URL (canonical, hreflang, Open Graph, JSON-LD, sitemap, robots.txt)
contains the site origin. This script replaces the current origin with the new one
in all those files and writes or removes the CNAME file that GitHub Pages reads.

    python scripts/set_domain.py skylolerr.dev        # custom domain, writes CNAME
    python scripts/set_domain.py skylolerr.github.io  # back to GitHub Pages, removes CNAME
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = "skylolerr.github.io"
FILES = ["**/*.html", "sitemap.xml", "robots.txt"]
DOMAIN = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


def current_domain() -> str:
    cname = ROOT / "CNAME"
    return cname.read_text(encoding="utf-8").strip() if cname.exists() else DEFAULT


def main() -> int:
    if len(sys.argv) != 2 or not DOMAIN.match(sys.argv[1].lower()):
        print(__doc__)
        return 2
    new = sys.argv[1].lower()
    old = current_domain()
    if new == old:
        print(f"The site already uses {new}.")
        return 0

    changed = 0
    for pattern in FILES:
        for path in sorted(ROOT.glob(pattern)):
            if ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            updated = text.replace(f"https://{old}/", f"https://{new}/")
            if updated != text:
                path.write_text(updated, encoding="utf-8", newline="\n")
                changed += 1
                print(f"updated {path.relative_to(ROOT)}")

    cname = ROOT / "CNAME"
    if new == DEFAULT:
        cname.unlink(missing_ok=True)
        print("removed CNAME")
    else:
        cname.write_text(new + "\n", encoding="utf-8", newline="\n")
        print(f"wrote CNAME: {new}")
    print(f"{old} -> {new}: {changed} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
