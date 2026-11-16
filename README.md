# Google News Lead Slot Observatory

Who does Google News put on top when several outlets cover the same story?
This repo audits the lead slot of Google News story cards in four country editions
(United States, France, Germany, Romania) and seven categories
(Business, Health, Nation, Politics, Science, Technology, World).

```
collector (carrot) ──► daily CSVs ──► pipeline/build_tables ──► pipeline/load_db ──► Postgres (alwaysdata)
                                                                                     │  db/views.sql
                                                              site (React) ◄── api (FastAPI on alwaysdata)
```

| Folder | What it is | Where it runs |
|---|---|---|
| `pipeline/` | Parses the daily Google News CSVs into tables and loads them into Postgres | carrot |
| `db/` | Postgres schema and the materialized views the site reads | alwaysdata Postgres |
| `api/` | Read-only JSON API over the views (FastAPI) | alwaysdata |
| `site/` | The public dashboard (React + Vite + Recharts) | GitHub Pages or alwaysdata |

Raw data never goes in the repo (see `.gitignore`).

## 1. Build the tables (carrot)

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m gnobs.build_tables ../../data/daily_news_csv ../out_news_tables
cat ../out_news_tables/parse_report.txt
```

Reads only the FR, Germany, Romania and US folders, the 7 category folders and 2026 files.
`parse_report.txt` says how well the story clusters were split into outlets.

## 2. Load into Postgres

Create a PostgreSQL database in the alwaysdata admin (Databases > PostgreSQL), then:

```bash
export DATABASE_URL='postgresql://USER:PASSWORD@postgresql-ACCOUNT.alwaysdata.net/DBNAME'
python -m gnobs.load_db ../out_news_tables
```

This creates the tables (`db/schema.sql`), replaces their content, and rebuilds the views (`db/views.sql`).
Re-run steps 1 and 2 whenever new data is collected.

Main views: `mv_kpi`, `mv_sources`, `mv_sources_by_category`, `mv_concentration_monthly`,
`mv_category_overview`, `mv_top_outlets`, `mv_top_outlets_by_category`, `mv_coverage_daily`.
"Fair" lead rates count only stories with at least two outlets.

## 3. Run the API

Locally:

```bash
cd api
pip install -r requirements.txt
DATABASE_URL=... uvicorn main:app --reload      # http://localhost:8000/api/kpi
```

On alwaysdata: upload the `api/` folder, install the requirements, and add a site of type
**Python ASGI** (or "User program") with command
`uvicorn main:app --host :: --port $PORT`, working directory the `api/` folder, and the
environment variables `DATABASE_URL` and `ALLOWED_ORIGINS` (the site's address, e.g.
`https://USERNAME.github.io`).

Endpoints: `/api/health`, `/api/kpi`, `/api/concentration_monthly`,
`/api/concentration_monthly_by_category`, `/api/category_overview`, `/api/top_outlets`,
`/api/top_outlets_by_category`, `/api/coverage_daily`, `/api/outlet/{edition}/{outlet}`.

## 4. Run the site

```bash
cd site
cp .env.example .env          # set VITE_API_URL
npm install
npm run dev                   # http://localhost:5173
npm run build                 # static files in site/dist
```

GitHub Pages: set the repository variable `API_URL`, enable Pages with source "GitHub Actions";
`.github/workflows/deploy-site.yml` publishes on every push to `main` that touches `site/`.

## Notes on the data

- Each story is one card from a non-personalized Google News topic feed, collected once a day:
  one lead article plus up to four related articles from other outlets.
- Single-article stories have only one outlet, which leads by default; use the fair lead rate.
- Outlet names are as Google writes them; variants of one outlet are not merged yet.
