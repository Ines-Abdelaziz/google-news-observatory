"""
Read-only JSON API over the observatory's Postgres views.

Run locally:   DATABASE_URL=... uvicorn main:app --reload
On alwaysdata: see README (site type "Python ASGI", command: uvicorn main:app --host :: --port $PORT)
"""
import os
import time

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row

DATABASE_URL = os.environ["DATABASE_URL"]
# comma-separated origins allowed to call the API, e.g. https://you.github.io
ALLOWED_ORIGINS = [o for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o]
CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "3600"))

# endpoint name -> SQL. Only these views can be read.
QUERIES = {
    "kpi": "SELECT * FROM mv_kpi",
    "concentration_monthly": "SELECT * FROM mv_concentration_monthly WHERE category = 'All' ORDER BY country, month",
    "concentration_monthly_by_category": "SELECT * FROM mv_concentration_monthly ORDER BY country, category, month",
    "category_overview": "SELECT * FROM mv_category_overview ORDER BY category, country",
    "top_outlets": "SELECT * FROM mv_top_outlets ORDER BY country, leads DESC",
    "top_outlets_by_category": "SELECT * FROM mv_top_outlets_by_category ORDER BY country, category, leads DESC",
    "coverage_daily": "SELECT * FROM mv_coverage_daily ORDER BY country, date",
}

app = FastAPI(title="Google News Lead Slot Observatory API")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET"], allow_headers=["*"])

_cache: dict[str, tuple[float, list]] = {}


def run(sql: str, params: tuple = ()) -> list[dict]:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        return conn.execute(sql, params).fetchall()


@app.get("/api/health")
def health():
    return {"ok": bool(run("SELECT 1 AS ok"))}


@app.get("/api/outlet/{country}/{outlet}")
def outlet(country: str, outlet: str):
    """Monthly leads and appearances of one outlet in one edition."""
    return run(
        """SELECT to_char(s.file_date, 'YYYY-MM') AS month, s.category,
                  count(*) AS appearances, count(*) FILTER (WHERE i.position = 0) AS leads
           FROM cluster_items i JOIN stories s USING (story_id) JOIN editions e ON e.country = s.country
           WHERE e.label = %s AND i.outlet = %s
           GROUP BY 1, 2 ORDER BY 1, 2""",
        (country, outlet),
    )


@app.get("/api/{name}")
def view(name: str):
    if name not in QUERIES:
        raise HTTPException(404, f"unknown dataset {name}")
    hit = _cache.get(name)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    rows = run(QUERIES[name])
    _cache[name] = (time.time(), rows)
    return rows
