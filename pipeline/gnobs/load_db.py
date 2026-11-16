#!/usr/bin/env python3
"""
Load the tables written by build_tables.py into Postgres and refresh the views.

Usage (on carrot, after build_tables.py):
    export DATABASE_URL='postgresql://USER:PASSWORD@postgresql-ACCOUNT.alwaysdata.net/DBNAME'
    python -m gnobs.load_db out_news_tables

Replaces the content of the tables on each run (full reload), then refreshes
every materialized view defined in db/views.sql.
"""
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "db" / "schema.sql"
VIEWS = ROOT / "db" / "views.sql"


def nn(v):
    """pandas NaN / empty string -> None for Postgres."""
    if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
        return None
    return v


def copy_rows(cur, table, columns, rows):
    with cur.copy(f"COPY {table} ({', '.join(columns)}) FROM STDIN") as cp:
        for r in rows:
            cp.write_row([nn(v) for v in r])


def main(tables_dir):
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("Set DATABASE_URL first (see the docstring).")
    d = Path(tables_dir)

    stories = pd.read_csv(d / "stories.csv.gz", dtype=str, keep_default_na=False)
    items = pd.read_csv(d / "cluster_items.csv.gz", dtype=str, keep_default_na=False)
    coverage = pd.read_csv(d / "coverage.csv", dtype=str, keep_default_na=False)
    print(f"{len(stories)} stories, {len(items)} cluster items, {len(coverage)} coverage rows")

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(SCHEMA.read_text())
        cur.execute("TRUNCATE cluster_items, stories, coverage")

        copy_rows(cur, "stories",
                  ["story_id", "country", "category", "file_date", "rank_in_file", "title",
                   "lead_outlet", "lead_website", "published_at", "url", "cluster_size"],
                  stories[["story_id", "country", "topic_folder", "file_date", "rank_in_file", "title",
                           "publisher_name", "publisher_website", "published_date", "url",
                           "cluster_size"]].itertuples(index=False))
        print("stories loaded")
        copy_rows(cur, "cluster_items", ["story_id", "position", "headline", "outlet", "parse"],
                  items[["story_id", "position", "headline", "outlet", "parse"]].itertuples(index=False))
        print("cluster items loaded")
        copy_rows(cur, "coverage", ["country", "category", "date", "n_stories"],
                  coverage[["country", "topic", "date", "n_stories"]].itertuples(index=False))
        print("coverage loaded")

        cur.execute(VIEWS.read_text())  # (re)creates the views, which computes them
        conn.commit()
    print("views refreshed - done")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
