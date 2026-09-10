#!/usr/bin/env python3
"""
Generate Pinterest pin images + a bulk-upload CSV for all 19 recipes.

For each recipe, composites a 1000x1500 JPEG (pins/<slug>.jpg):
  - top 940px: the recipe's @2x photo (images/<slug>@2x.jpg), cover-cropped
  - a cream (#f5ead8) panel: title (Poppins 700) + a grey meta line
    (total time + yield), centered as one block in the panel
  - a coral (#ff6d6d) footer bar: "sweetsaltyrecipes.com"

Then writes pins/pinterest-bulk-upload.csv for Pinterest's bulk-upload
tool, with publish dates spread evenly starting tomorrow at 20:00.

Sources of truth (never invents content):
  - js/main.js            -> ALL_RECIPES: title, image, tags, page, desc
  - data/recipe-meta.json -> totalTime, recipeYield
  - data/pin-titles.json  -> hand-written, search-friendly pin titles,
                              keyed by slug. Falls back to the site title
                              if a recipe has no entry — flagged, not
                              silently guessed.

Fonts: Poppins is only shipped as woff2 (see fonts/README / CLAUDE.md).
Pillow can't rasterize woff2 directly, so each weight needed is
converted to TTF once via fontTools and cached in scripts/.font-cache/
(gitignored — regenerated from the real woff2 source, never itself a
source of truth).

Usage:
  python3 scripts/generate_pins.py
"""
import argparse
import csv
import datetime
import json
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_schema import parse_all_recipes, slug_for, MAIN_JS, TYPE_TAGS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "fonts"
FONT_CACHE_DIR = ROOT / "scripts" / ".font-cache"
IMAGES_DIR = ROOT / "images"
PINS_DIR = ROOT / "pins"
RECIPE_META = ROOT / "data" / "recipe-meta.json"
PIN_TITLES = ROOT / "data" / "pin-titles.json"
SITE_URL = "https://sweetsaltyrecipes.com"

PIN_W, PIN_H = 1000, 1500
PHOTO_H = 940
FOOTER_H = 64
CREAM = "#f5ead8"
CORAL = "#ff6d6d"
INK = "#2b2620"
GREY = "#8a8377"

TITLE_MAX = 100
DESC_MAX = 500
# Pinterest's bulk scheduler rejects any pin dated more than 2 weeks out, and
# rejects the whole upload if a single row is invalid. Dates start tomorrow, so
# the furthest pin is (1 + PUBLISH_SPAN_DAYS) days out — keep that at 12 or under
# to leave slack for upload lag and timezones. 11 => furthest pin +12 days.
PUBLISH_SPAN_DAYS = 11
PUBLISH_HOUR = 20

BOARD_MAP = {
    "Cookie": "Cookie Recipes",
    "Pastry": "Pastry Recipes",
    "Cake": "Dessert Recipes",
    "Dessert": "Dessert Recipes",
    "Breakfast": "Breakfast Recipes",
}


def woff2_to_ttf(weight):
    """Convert fonts/poppins-<weight>.woff2 to a cached TTF, once."""
    FONT_CACHE_DIR.mkdir(exist_ok=True)
    cached = FONT_CACHE_DIR / f"poppins-{weight}.ttf"
    if cached.exists():
        return str(cached)
    src = FONTS_DIR / f"poppins-{weight}.woff2"
    if not src.exists():
        sys.exit(f"ERROR: {src} not found")
    font = TTFont(src)
    font.flavor = None  # strip woff2 compression -> plain TTF/OTF outlines
    font.save(str(cached))
    return str(cached)


def parse_iso_duration(iso):
    """'PT2H40M' -> '2 hr 40 min', 'PT45M' -> '45 min', 'PT1H' -> '1 hr'."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso)
    if not m:
        return iso
    hours, minutes = m.groups()
    parts = []
    if hours:
        parts.append(f"{hours} hr")
    if minutes:
        parts.append(f"{minutes} min")
    return " ".join(parts) if parts else iso


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def cover_crop(img, target_w, target_h):
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        # source is relatively wider -> crop left/right
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        # source is relatively taller -> crop top/bottom
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))
    return img.resize((target_w, target_h), Image.LANCZOS)


def build_pin_image(recipe, title, meta_line, out_path):
    photo_path = IMAGES_DIR / f"{slug_for(recipe['page'])}@2x.jpg"
    if not photo_path.exists():
        return f"missing {photo_path.relative_to(ROOT)}"

    canvas = Image.new("RGB", (PIN_W, PIN_H), CREAM)

    photo = cover_crop(Image.open(photo_path).convert("RGB"), PIN_W, PHOTO_H)
    canvas.paste(photo, (0, 0))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, PIN_H - FOOTER_H, PIN_W, PIN_H], fill=CORAL)

    meta_font = ImageFont.truetype(woff2_to_ttf(400), 32)
    footer_font = ImageFont.truetype(woff2_to_ttf(600), 30)

    margin = 60
    max_text_width = PIN_W - 2 * margin
    line_gap = 10

    # Shrink the title font until it wraps to 2 lines or fewer, so an
    # unexpectedly long title (pin-titles.json is hand-written, not
    # length-constrained beyond the 100-char CSV cap) can't crowd the
    # panel — fall back to the smallest size tried if it still needs 3.
    ttf_700 = woff2_to_ttf(700)
    for size in (58, 52, 46, 40, 36):
        title_font = ImageFont.truetype(ttf_700, size)
        title_lines = wrap_text(draw, title, title_font, max_text_width)
        if len(title_lines) <= 2:
            break
    title_line_h = title_font.getbbox("Ag")[3] + line_gap
    meta_line_h = meta_font.getbbox("Ag")[3]
    block_gap = 24  # space between title block and meta line
    block_h = len(title_lines) * title_line_h - line_gap + block_gap + meta_line_h

    panel_top = PHOTO_H
    panel_h = PIN_H - FOOTER_H - PHOTO_H
    y = panel_top + (panel_h - block_h) / 2

    for line in title_lines:
        w = draw.textlength(line, font=title_font)
        draw.text(((PIN_W - w) / 2, y), line, font=title_font, fill=INK)
        y += title_line_h
    y += block_gap - line_gap
    w = draw.textlength(meta_line, font=meta_font)
    draw.text(((PIN_W - w) / 2, y), meta_line, font=meta_font, fill=GREY)

    footer_text = "sweetsaltyrecipes.com"
    fw = draw.textlength(footer_text, font=footer_font)
    fh = footer_font.getbbox("Ag")[3]
    draw.text(
        ((PIN_W - fw) / 2, PIN_H - FOOTER_H + (FOOTER_H - fh) / 2 - footer_font.getbbox("Ag")[1]),
        footer_text, font=footer_font, fill="#ffffff",
    )

    PINS_DIR.mkdir(exist_ok=True)
    canvas.save(out_path, "JPEG", quality=88)
    return None


def board_for(tags):
    for tag in tags:
        if tag in BOARD_MAP:
            return BOARD_MAP[tag]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="process a single recipe by slug")
    args = ap.parse_args()

    all_recipes = parse_all_recipes(MAIN_JS.read_text(encoding="utf-8"))
    meta_all = load_json(RECIPE_META)
    pin_titles = load_json(PIN_TITLES)

    missing_meta = [slug_for(r["page"]) for r in all_recipes if slug_for(r["page"]) not in meta_all]
    if missing_meta:
        sys.exit("ERROR: data/recipe-meta.json is missing entries for: " + ", ".join(missing_meta))

    if args.only:
        all_recipes = [r for r in all_recipes if slug_for(r["page"]) == args.only]
        if not all_recipes:
            sys.exit(f"ERROR: no ALL_RECIPES entry with slug '{args.only}'")

    no_override = []
    csv_rows = []

    n = len(all_recipes)
    now = datetime.date.today()
    start = now + datetime.timedelta(days=1)

    for i, recipe in enumerate(all_recipes):
        slug = slug_for(recipe["page"])
        meta = meta_all[slug]

        title = pin_titles.get(slug)
        if not title:
            no_override.append(slug)
            title = recipe["title"]
        title = title[:TITLE_MAX]

        human_time = parse_iso_duration(meta["totalTime"])
        meta_line = f"Total: {human_time}  •  Yield: {meta['recipeYield']}"

        out_path = PINS_DIR / f"{slug}.jpg"
        problem = build_pin_image(recipe, title, meta_line, out_path)
        if problem:
            print(f"  ✗ {slug}: {problem}")
            continue
        print(f"  ✓ {slug}")

        day_offset = round(i * PUBLISH_SPAN_DAYS / (n - 1)) if n > 1 else 0
        publish_dt = datetime.datetime.combine(
            start + datetime.timedelta(days=day_offset),
            datetime.time(PUBLISH_HOUR, 0, 0),
        )

        description = f"{recipe['desc']}. Total time: {human_time}. Yield: {meta['recipeYield']}."
        description = description[:DESC_MAX]

        csv_rows.append({
            "Title": title,
            "Media URL": f"{SITE_URL}/pins/{slug}.jpg",
            "Pinterest board": board_for(recipe["tags"]),
            "Thumbnail": "",
            "Description": description,
            "Link": f"{SITE_URL}/{recipe['page']}",
            "Publish date": publish_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "Keywords": ", ".join(recipe["tags"]),
        })

    csv_path = PINS_DIR / "pinterest-bulk-upload.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Title", "Media URL", "Pinterest board", "Thumbnail",
                        "Description", "Link", "Publish date", "Keywords"],
            lineterminator="\r\n",
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\nWrote {len(csv_rows)} pin(s) + {csv_path.relative_to(ROOT)}")
    if no_override:
        print(f"\n{len(no_override)} recipe(s) using the site title as a fallback "
              f"(no entry in data/pin-titles.json):")
        for slug in no_override:
            print(f"  - {slug}")


if __name__ == "__main__":
    main()
