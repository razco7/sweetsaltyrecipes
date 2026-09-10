#!/usr/bin/env python3
"""
Generate sitemap.xml from the site's actual page inventory.

Discovers the same set of real content pages as scripts/add_seo_tags.py
(every *.html at the root, in recipe-pages/, and in collection-pages/,
excluding 404.html and the Search Console verification stub). lastmod
comes from each file's last git commit date, falling back to today for
an uncommitted/new file — same approach as dateModified in
scripts/generate_schema.py.

Safe to re-run any time a page is added, removed, or edited — fully
overwrites sitemap.xml (there's nothing hand-maintained in it to preserve).

Usage:
  python3 scripts/generate_sitemap.py
"""
import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://sweetsaltyrecipes.com"
EXCLUDE = {"404.html", "recipe-pages/savory-libyan-kaak.html"}


def discover_pages():
    # Only *.html patterns are globbed, so pins/*.jpg (Pinterest pin
    # images, see generate_pins.py) is never picked up here — they're
    # images, not pages, and shouldn't be in the page sitemap.
    pages = []
    for pattern in ("*.html", "recipe-pages/*.html", "collection-pages/*.html"):
        for p in sorted(ROOT.glob(pattern)):
            rel = p.relative_to(ROOT).as_posix()
            if rel in EXCLUDE:
                continue
            pages.append(rel)
    return pages


def canonical_url(rel_path):
    if rel_path == "index.html":
        return f"{SITE_URL}/"
    return f"{SITE_URL}/{rel_path}"


def git_last_commit_date(rel_path):
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", rel_path],
            cwd=ROOT, capture_output=True, text=True, timeout=5, check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return result.stdout.strip() or None


def main():
    pages = discover_pages()
    today = datetime.date.today().isoformat()

    entries = []
    for rel_path in pages:
        lastmod = git_last_commit_date(rel_path) or today
        entries.append((canonical_url(rel_path), lastmod))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")

    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote sitemap.xml with {len(entries)} URLs")


if __name__ == "__main__":
    main()
