#!/usr/bin/env python3
"""
Rewrite the site header (`<nav class="navbar">` + the `<div class="mobile-nav">`
drawer) on every content page from one template here.

Why: the header is copied into ~40 pages with no include mechanism, so it drifts
(whitespace, stale links) and any change means editing every file by hand. This
script is the single source of truth — edit NAV_TEMPLATE / the collection lists
below, re-run, commit.

It replaces everything from `<nav class="navbar">` up to (but not including)
`<div class="search-overlay" id="searchOverlay">`, so the search overlay, footer,
and page body are never touched. Pages without `<nav class="navbar">` (404.html,
redirect stubs) are skipped automatically.

Relative paths are computed per page depth:
  - root pages (index.html, about.html, …):      href="all-recipes.html",  collection href="collection-pages/x.html"
  - recipe-pages/ and collection-pages/ (depth 1): href="../all-recipes.html"
      · from collection-pages/, sibling collections link bare: href="x.html"
      · from recipe-pages/,      collections link: href="../collection-pages/x.html"

Idempotent — safe to re-run any time.

Usage:
  python3 scripts/generate_nav.py            # rewrite every page
  python3 scripts/generate_nav.py --check    # report which pages would change, write nothing
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Collections shown in the "All collections" menu, grouped by category.
# (label, slug) — slug is the collection-pages/<slug>-recipes.html basename stem.
# Only collections with a dedicated page AND at least one recipe belong here.
MENU = [
    ("Type", [
        ("Cookies", "cookie-recipes"),
        ("Pastry", "pastry-recipes"),
        ("Breakfast", "breakfast-recipes"),
    ]),
    ("Country", [
        ("France", "france-recipes"),
        ("Italy", "italy-recipes"),
        ("Germany", "germany-recipes"),
        ("Austria", "austria-recipes"),
        ("Denmark", "denmark-recipes"),
        ("Netherlands", "netherlands-recipes"),
        ("USA", "usa-recipes"),
        ("Middle East", "middle-east-recipes"),
    ]),
    ("Taste", [
        ("Sweet", "sweet-recipes"),
        ("Salty", "salty-recipes"),
    ]),
    ("Level", [
        ("Easy", "easy-level-recipes"),
        ("Moderate", "moderate-level-recipes"),
        ("Hard", "hard-level-recipes"),
    ]),
]

NAV_RE = re.compile(
    r'<nav class="navbar">.*?(?=<div class="search-overlay" id="searchOverlay">)',
    re.DOTALL,
)


def page_prefix(rel_path: str) -> str:
    """'' for a root page, '../' for a page one directory deep."""
    return "../" if "/" in rel_path else ""


def collection_prefix(rel_path: str) -> str:
    if rel_path.startswith("collection-pages/"):
        return ""
    if "/" in rel_path:
        return "../collection-pages/"
    return "collection-pages/"


def build_nav(rel_path: str) -> str:
    p = page_prefix(rel_path)
    c = collection_prefix(rel_path)

    # Desktop mega-menu columns
    desktop_cols = []
    for label, items in MENU:
        rows = "\n".join(
            f'              <a href="{c}{slug}.html">{text}</a>' for text, slug in items
        )
        desktop_cols.append(
            f'            <div class="nav-mega-col">\n'
            f'              <span class="nav-mega-heading">{label}</span>\n'
            f'{rows}\n'
            f'            </div>'
        )
    desktop_cols = "\n".join(desktop_cols)

    # Mobile: one collapsible section, headings interleaved
    mobile_rows = []
    for label, items in MENU:
        mobile_rows.append(f'    <span class="mobile-mega-heading">{label}</span>')
        mobile_rows.extend(
            f'    <a href="{c}{slug}.html">{text}</a>' for text, slug in items
        )
    mobile_rows = "\n".join(mobile_rows)

    return f'''<nav class="navbar">
  <div class="container">
    <a href="{p}index.html" class="nav-logo">
      <img src="{p}images/logo-nav.svg" alt="Sweet / Salty">
    </a>
    <div class="nav-right">
      <button class="btn-search" id="searchBtn" aria-label="Search">
        <img src="{p}images/icon-search.svg" alt="Search">
      </button>
      <div class="nav-links">
        <a href="{p}all-recipes.html">All recipes</a>
        <div class="nav-dropdown">
          <button class="nav-dropdown-btn">All collections</button>
          <div class="nav-dropdown-menu nav-mega">
{desktop_cols}
          </div>
        </div>
        <a href="{p}about.html">About</a>
        <a href="{p}contact.html">Contact</a>
        <a href="https://buymeacoffee.com/razco7" target="_blank" class="btn-coffee">Buy us a coffee</a>
      </div>
      <button class="nav-toggle" id="navToggle" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</nav>

<div class="mobile-nav" id="mobileNav">
  <a href="{p}all-recipes.html">All recipes</a>
  <span class="mobile-dropdown-label">All collections</span>
  <div class="mobile-dropdown-items mobile-mega">
{mobile_rows}
  </div>
  <a href="{p}about.html">About</a>
  <a href="{p}contact.html">Contact</a>
  <a href="https://buymeacoffee.com/razco7" target="_blank" class="btn-coffee">Buy us a coffee</a>
</div>

'''


def discover_pages():
    pages = []
    for pattern in ("*.html", "recipe-pages/*.html", "collection-pages/*.html"):
        for path in sorted(ROOT.glob(pattern)):
            pages.append(path.relative_to(ROOT).as_posix())
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    changed, skipped = [], []
    for rel_path in discover_pages():
        path = ROOT / rel_path
        html = path.read_text(encoding="utf-8")
        if '<nav class="navbar">' not in html:
            skipped.append(rel_path)
            continue
        new_html = NAV_RE.sub(lambda _: build_nav(rel_path), html, count=1)
        if new_html != html:
            changed.append(rel_path)
            if not args.check:
                path.write_text(new_html, encoding="utf-8")

    verb = "Would rewrite" if args.check else "Rewrote"
    print(f"{verb} the header on {len(changed)} page(s):")
    for p in changed:
        print(f"  ✓ {p}")
    if skipped:
        print(f"\nSkipped {len(skipped)} page(s) with no navbar: {', '.join(skipped)}")


if __name__ == "__main__":
    main()
