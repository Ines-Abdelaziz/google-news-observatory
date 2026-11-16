# Google News Lead Slot Observatory

Who does Google News put on top when several outlets cover the same story?
This repo audits the lead slot of Google News story cards in four country editions
(United States, France, Germany, Romania) and seven categories
(Business, Health, Nation, Politics, Science, Technology, World).

```
carrot:  daily CSVs ──► build_tables (pandas) ──► export_json (DuckDB) ──► site/public/data/*.json
                                                                                  │  git push
                                                                     GitHub Pages: static React site
```

| Folder | What it is |
|---|---|
| `pipeline/gnobs/build_tables.py` | Parses the daily Google News CSVs: one row per story, one row per article in each story card, coverage per day |
| `pipeline/sql/aggregates.sql` | The aggregates the site shows, in DuckDB SQL |
| `pipeline/gnobs/export_json.py` | Runs the SQL with DuckDB and writes the JSON files into the site |
| `site/` | The dashboard: React + Vite + Recharts, fully static |

Raw data never goes in the repo (see `.gitignore`); only the small aggregate JSON in `site/public/data/` does.

## Update the data (on carrot)

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. parse the daily CSVs (a few minutes)
python -m gnobs.build_tables ../../data/daily_news_csv ../out_news_tables
cat ../out_news_tables/parse_report.txt

# 2. compute the aggregates and write the site's JSON (keep a DuckDB file for your own queries)
python -m gnobs.export_json ../out_news_tables ../site/public/data --db ../out_news_tables/observatory.duckdb

# 3. publish
cd .. && git add site/public/data && git commit -m "Update data" && git push
```

`build_tables` reads only the FR, Germany, Romania and US folders, the 7 category folders and
2026 files. `parse_report.txt` says how well the story cards were split into outlets.

To explore the data yourself: `duckdb out_news_tables/observatory.duckdb`, then query the tables
`stories`, `cluster_items`, `coverage`, `sources`, `sources_by_category`, and the exported ones.

## Run the site

```bash
cd site
npm install
npm run dev        # http://localhost:5173
npm run build      # static files in site/dist
```

GitHub Pages: in the repository settings, enable Pages with source "GitHub Actions".
`.github/workflows/deploy-site.yml` publishes on every push to `main` that touches `site/`.

## Notes on the data

- Each story is one card from a non-personalized Google News topic feed, collected once a day:
  one lead article plus up to four related articles from other outlets.
- Lead rate = leads ÷ appearances. Single-article stories have only one outlet, which leads by
  default, so the **fair lead rate** counts only stories with at least two outlets.
- Outlet names are as Google writes them; variants of one outlet are not merged yet.
