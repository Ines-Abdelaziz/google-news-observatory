# Maintaining the observatory

How to update the data and publish the site. Raw data stays on the collection server; only the
aggregated JSON in `site/public/data/` is committed.

```
daily CSVs ─► build_tables ─► export_json (DuckDB) ─┐
                            ─► text_analyses ────────┼─► site/public/data/*.json ─► git push ─► GitHub Pages
                            ─► events (optional) ────┘
```

## Update the data (on the collection server)

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. parse the daily CSVs into tables (a few minutes)
python -m gnobs.build_tables PATH/TO/daily_news_csv ../out_news_tables
cat ../out_news_tables/parse_report.txt

# 2. all SQL aggregates + outlet labels (a few minutes)
python -m gnobs.export_json ../out_news_tables ../site/public/data --db ../out_news_tables/observatory.duckdb

# 3. keywords, names, countries mentioned (a few minutes)
python -m gnobs.text_analyses ../out_news_tables ../site/public/data

# 4. optional: same events across editions (needs sentence-transformers; faster on a GPU)
pip install sentence-transformers
python -m gnobs.events ../out_news_tables ../site/public/data

cd .. && git add site/public/data && git commit -m "Update data" && git push
```

Check after each run:
- `out_news_tables/parse_report.txt`: "first cluster outlet == publisher_name" close to 100%, few
  "heuristic"/"failed" parses. It also lists Google's "full coverage" link wordings.
- `out_news_tables/outlet_aliases.csv`: outlet names merged because they share a website
  (e.g. "Ntv" → "n-tv.de"). Disable with `--no-merge`.
- `out_news_tables/labels_review.csv`: the 300 most frequent outlets per edition with their
  automatic country and type. Correct mistakes in `pipeline/labels/outlet_labels.csv`, then rerun step 2.

## Outlet labels

`pipeline/gnobs/labels.py` labels each outlet with a country and a type, in this order:
1. `pipeline/labels/outlet_labels.csv` (manual, wins over everything),
2. the list of known outlets in `labels.py` (by website),
3. the website's country code (.fr, .de, .ro, .co.uk…) for the country only.

Types: commercial, public service, wire agency, aggregator, state-controlled, other (= not labelled).
The site shows how much of each edition's lead slot is labelled (Data & methods tab).

## Test without the real data

```bash
cd pipeline
python tests/make_synthetic.py /tmp/fake_daily_news_csv
python -m gnobs.build_tables /tmp/fake_daily_news_csv /tmp/fake_tables
python -m gnobs.export_json /tmp/fake_tables /tmp/fake_json
python -m gnobs.text_analyses /tmp/fake_tables /tmp/fake_json
```

Copy `/tmp/fake_json/*.json` into `site/public/data/` to look at the site with fake data (don't commit them).

## Explore the data

```bash
duckdb out_news_tables/observatory.duckdb
```

Base tables: `stories`, `cluster_items`, `coverage`, `editions`, `outlet_alias`, `outlet_labels`.
Every aggregate in `pipeline/sql/aggregates.sql` and `pipeline/sql/labels.sql` is also a table.

## Run the site locally

```bash
cd site
npm install
npm run dev      # http://localhost:5173
npm run build    # static files in site/dist
```

Tabs: Overview, Lead slot, Outlets, Agenda, Timing, Feed design, Compare editions, Data & methods.
A view whose JSON file is missing says "Not computed yet".

## Publish

In the repository settings, enable Pages with source "GitHub Actions".
`.github/workflows/deploy-site.yml` builds and publishes the site on every push to `main` that
touches `site/`. A private repository needs GitHub Pro for Pages.

## Add a new aggregate

1. Add a `CREATE TABLE ... AS` block to `pipeline/sql/aggregates.sql` (or `labels.sql` if it needs labels).
2. Add its name to `EXPORT` (or `LABEL_EXPORT`) in `pipeline/gnobs/export_json.py`.
3. Load it in a tab with `useData('<name>')` (see `site/src/tabs/`).
