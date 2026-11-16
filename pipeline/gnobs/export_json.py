#!/usr/bin/env python3
"""
Compute the aggregates with DuckDB and write the JSON files the website reads.

Usage (on carrot, after build_tables):
    python -m gnobs.export_json ../out_news_tables ../site/public/data

Reads stories.csv.gz, cluster_items.csv.gz and coverage.csv from the tables folder,
runs sql/aggregates.sql, and writes one <table>.json per aggregate. Optionally keeps
a DuckDB file for your own queries:  --db ../out_news_tables/observatory.duckdb
"""
import argparse
import json
from pathlib import Path

import duckdb

SQL = Path(__file__).resolve().parents[1] / "sql" / "aggregates.sql"
EDITIONS = [("US", "United States", 1), ("FR", "France", 2), ("Germany", "Germany", 3), ("Romania", "Romania", 4)]
EXPORT = ["kpi", "concentration_monthly", "category_overview", "top_outlets",
          "top_outlets_by_category", "coverage_daily"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tables", help="folder written by build_tables")
    ap.add_argument("out", help="where to write the JSON files (site/public/data)")
    ap.add_argument("--db", default=":memory:", help="optional DuckDB file to keep the tables")
    a = ap.parse_args()

    t, out = Path(a.tables), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(a.db)

    con.execute("CREATE OR REPLACE TABLE editions (country VARCHAR, label VARCHAR, sort INT)")
    con.executemany("INSERT INTO editions VALUES (?, ?, ?)", EDITIONS)
    con.execute(f"""
        CREATE OR REPLACE TABLE stories AS
        SELECT story_id, country, topic_folder AS category, file_date::DATE AS file_date,
               rank_in_file::INT AS rank_in_file, title,
               coalesce(publisher_name, '') AS lead_outlet, publisher_website AS lead_website,
               try_cast(published_date AS TIMESTAMP) AS published_at, url, cluster_size::INT AS cluster_size
        FROM read_csv('{t / "stories.csv.gz"}', all_varchar = true)""")
    con.execute(f"""
        CREATE OR REPLACE TABLE cluster_items AS
        SELECT story_id, position::INT AS position, headline, coalesce(outlet, '') AS outlet, parse
        FROM read_csv('{t / "cluster_items.csv.gz"}', all_varchar = true)""")
    con.execute(f"""
        CREATE OR REPLACE TABLE coverage AS
        SELECT country, topic AS category, date::DATE AS date, n_stories::INT AS n_stories
        FROM read_csv('{t / "coverage.csv"}', all_varchar = true)""")

    for name in EXPORT + ["sources", "sources_by_category"]:
        con.execute(f"DROP TABLE IF EXISTS {name}")
    con.execute(SQL.read_text())

    for name in EXPORT:
        rel = con.execute(f"SELECT * FROM {name}")
        cols = [d[0] for d in rel.description]
        rows = [dict(zip(cols, r)) for r in rel.fetchall()]
        path = out / f"{name}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False, default=str, separators=(",", ":")))
        print(f"{path}  {len(rows)} rows")


if __name__ == "__main__":
    main()
