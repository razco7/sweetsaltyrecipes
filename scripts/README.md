# Scripts

One-off maintenance tools for the site's SEO foundation. Nothing here runs
as part of a build — the site itself has none (see the root `CLAUDE.md`).
Run these by hand after editing recipes, or let the GitHub Actions
workflow run the Search Console one on a schedule.

```bash
pip install -r scripts/requirements.txt
```

## generate_schema.py

Regenerates the `Recipe` JSON-LD block on every `recipe-pages/*.html`
page. Re-run it whenever a recipe's ingredients, instructions, tags, or
`data/recipe-meta.json` entry changes.

```bash
python3 scripts/generate_schema.py              # all 19 pages
python3 scripts/generate_schema.py --only pizza # a single page
python3 scripts/generate_schema.py --check       # report only
```

## generate_sitemap.py

Rewrites `sitemap.xml` from the site's actual page inventory. Re-run it
whenever a page is added or removed.

```bash
python3 scripts/generate_sitemap.py
```

## generate_static_links.py

Refreshes the `<noscript>` fallback link list on `all-recipes.html` and
every `collection-pages/*.html` page, from `ALL_RECIPES` in `js/main.js`.
Re-run it whenever a recipe is added, removed, or re-tagged.

```bash
python3 scripts/generate_static_links.py
```

## add_seo_tags.py

Adds/refreshes `<link rel="canonical">` and `<meta name="description">`
on every real page, from each page's own `og:description`. Re-run it if a
page's OG description changes.

```bash
python3 scripts/add_seo_tags.py
```

## search_console_report.py

Pulls the last 28 days of Search Console data and writes a ranked report
(content gaps, striking-distance queries, top pages) to `reports/`.

### One-time setup: a Search Console service account

Search Console's API needs a Google Cloud service account — a "robot"
Google identity your own account grants read access to, so the script can
authenticate without your personal login or a browser OAuth flow.

1. **Create a Google Cloud project** (or use an existing one) at
   [console.cloud.google.com](https://console.cloud.google.com/).
2. **Enable the Search Console API**: APIs & Services > Library, search
   for "Google Search Console API", click Enable.
3. **Create a service account**: APIs & Services > Credentials > Create
   Credentials > Service account. Give it any name (e.g.
   `sweetsalty-search-console-reader`). No project role needed — it only
   needs access granted directly in Search Console (next step).
4. **Create a JSON key** for that service account: open it under
   Credentials, go to the Keys tab, Add Key > Create new key > JSON. This
   downloads a `.json` file — **treat it like a password**. Don't commit
   it; the conventional spot is `scripts/credentials/` in this repo,
   which is already in `.gitignore`.
5. **Grant the service account access in Search Console**: in
   [Search Console](https://search.google.com/search-console), select
   the `sweetsaltyrecipes.com` **Domain property** (not the old `www`
   URL-prefix one) > Settings > Users and permissions > Add user. Enter
   the service account's email address (looks like
   `sweetsalty-search-console-reader@your-project.iam.gserviceaccount.com`
   — find it on the service account's details page, or inside the JSON
   key file's `client_email` field). "Restricted" permission is enough —
   this script only reads data.

`GSC_SITE_URL` must match the property's identifier as the Search
Console **API** expects it, which is not the same as its URL in the
browser. Since `sweetsaltyrecipes.com` is a **Domain property**, that's
`sc-domain:sweetsaltyrecipes.com` — no `https://`, no trailing slash. (A
URL-prefix property would instead use its exact URL, e.g.
`https://sweetsaltyrecipes.com/`.) Using the wrong form doesn't error at
auth time — it authenticates fine and then fails with a 403
"insufficient permission" on the actual query, which looks like a
permissions problem rather than a formatting one.

### Running it locally

```bash
export GSC_SERVICE_ACCOUNT_FILE=scripts/credentials/service-account.json
export GSC_SITE_URL=sc-domain:sweetsaltyrecipes.com
python3 scripts/search_console_report.py
```

Writes `reports/YYYY-MM-DD-search-console.md`.

### Running it on a schedule (GitHub Actions)

`.github/workflows/search-console-report.yml` runs this weekly and
commits the resulting report. It needs two repository secrets (Settings
> Secrets and variables > Actions > New repository secret):

- `GSC_SERVICE_ACCOUNT_JSON` — the **entire contents** of the service
  account's JSON key file, pasted as the secret value.
- `GSC_SITE_URL` — `sc-domain:sweetsaltyrecipes.com`

The workflow writes that secret to a temporary file at runtime (never to
the repo) and points `GSC_SERVICE_ACCOUNT_FILE` at it.

## check_sitemap_status.py

A quick diagnostic: is Google actually fetching `sitemap.xml`, and are
there any warnings/errors? Uses the same credentials as
`search_console_report.py` above — no separate setup needed.

```bash
export GSC_SERVICE_ACCOUNT_FILE=scripts/credentials/service-account.json
export GSC_SITE_URL=sc-domain:sweetsaltyrecipes.com
python3 scripts/check_sitemap_status.py
```

Or on demand via GitHub Actions, without opening Search Console's UI at
all: `.github/workflows/check-sitemap-status.yml` (`workflow_dispatch`
only, no schedule) — trigger with `gh workflow run
check-sitemap-status.yml` and read the result with `gh run view <run-id>
--log`.

## generate_pins.py

Generates a Pinterest pin image (`pins/<slug>.jpg`, 1000×1500) for every
recipe — the `@2x` hero photo, a title + time/yield meta line on a cream
panel, a coral footer bar — plus `pins/pinterest-bulk-upload.csv` for
Pinterest's bulk-upload tool.

```bash
python3 scripts/generate_pins.py                 # every recipe + a full CSV
python3 scripts/generate_pins.py --only sachertorte  # one pin + a one-row CSV
```

Re-run it whenever a recipe's photo, tags, desc, or `data/recipe-meta.json`
entry changes, or after editing `data/pin-titles.json` — it's
idempotent, and `pins/` is committed (not gitignored) since the CSV
references the images by their live site URL.

**`--only <slug>` overwrites `pinterest-bulk-upload.csv` with just that
one row** — not a preview side effect, it's the point. After the initial
all-recipes upload, each new recipe is scheduled by uploading its own
one-row CSV, so the weekly pipeline runs `--only`. To rebuild the full
CSV (all recipes, dates restarting tomorrow), run the script with no
`--only` — but don't re-upload that or you'll double-schedule the pins
already queued on Pinterest.

- Pin **titles** come from `data/pin-titles.json` (`{"slug": "title"}`)
  — falls back to the site's own recipe title if a slug has no entry,
  and the script prints which ones fell back. The title font
  auto-shrinks (58px down to 36px) if it wraps past 2 lines, so an
  unexpectedly long title can't crowd the panel.
- **Fonts**: Pillow can't rasterize the site's woff2 files directly, so
  each weight needed gets converted to TTF once via fontTools and
  cached in `scripts/.font-cache/` (gitignored — regenerated from the
  real `fonts/*.woff2` source, delete it any time).
- **CSV publish dates** spread across 11 days starting tomorrow at 20:00
  (furthest pin ~12 days out). Pinterest's bulk scheduler **rejects any
  pin dated more than 2 weeks out, and rejects the entire upload if one
  row is invalid** — the 12-day ceiling leaves slack for upload lag and
  timezones. Re-running shifts every date forward relative to whatever
  "tomorrow" is when you run it, so generate the CSV right before
  uploading, not days ahead.
- **Pinterest board** is inferred from each recipe's type tag (Cookie /
  Pastry / Cake+Dessert / Breakfast) — a recipe untagged with one of
  those gets an empty board column, which Pinterest's bulk uploader
  will reject; that shouldn't currently happen, but if a future recipe
  only carries a country/Sweet-Salty/difficulty tag, add its type tag
  to `BOARD_MAP` in the script.
