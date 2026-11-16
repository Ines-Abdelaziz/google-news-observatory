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

from gnobs.labels import build_label_table

SQL = Path(__file__).resolve().parents[1] / "sql" / "aggregates.sql"
LABELS_SQL = Path(__file__).resolve().parents[1] / "sql" / "labels.sql"

# platforms that host many unrelated publishers: never merge names sharing these domains
SHARED_DOMAINS = ("news.google.com", "google.com", "youtube.com", "medium.com", "substack.com",
                  "blogspot.com", "wordpress.com", "facebook.com", "x.com", "twitter.com", "linkedin.com")

ALIAS_SQL = """
CREATE OR REPLACE TABLE outlet_alias AS
WITH named AS (
    SELECT country, lead_outlet AS outlet,
           regexp_replace(split_part(regexp_replace(lower(lead_website), '^[a-z]+://', ''), '/', 1),
                          '^(www[0-9]?|m|amp)[.]', '') AS dom,
           count(*) AS n
    FROM stories WHERE lead_outlet <> '' AND coalesce(lead_website, '') <> ''
    GROUP BY ALL
), per_name AS (
    SELECT country, outlet, arg_max(dom, n) AS dom, sum(n) AS n FROM named GROUP BY ALL
), canon AS (
    SELECT country, dom, arg_max(outlet, n) AS canonical, count(*) AS names FROM per_name GROUP BY ALL
)
SELECT p.country, p.outlet, c.canonical, p.dom AS domain, p.n AS leads_under_this_name
FROM per_name p JOIN canon c USING (country, dom)
WHERE c.names > 1 AND p.outlet <> c.canonical AND p.dom NOT IN ({shared})
"""
# folder name, label shown on the site, order, time zone of the edition
EDITIONS = [("US", "United States", 1, "America/New_York"), ("FR", "France", 2, "Europe/Paris"),
            ("Germany", "Germany", 3, "Europe/Berlin"), ("Romania", "Romania", 4, "Europe/Bucharest")]
LABEL_EXPORT = ["label_coverage", "origin_mix", "type_mix", "state_media",
                "world_outlets_across_editions", "world_edition_similarity"]
EXPORT = [
    # lead slot
    "kpi", "concentration_monthly", "category_overview", "top_outlets", "top_outlets_by_category",
    # agenda
    "section_mix_weekly", "story_lifespan", "section_overlap",
    # outlets
    "outlet_diversity_weekly", "outlet_churn_monthly", "coappearance_nodes", "coappearance_edges",
    "profile_outlets", "profile_monthly", "profile_categories", "profile_partners",
    # timing
    "publication_hours", "freshness", "weekday_mix",
    # feed design
    "cluster_size_monthly", "link_phrase_weekly", "feed_position", "coverage_daily",
    # headlines
    "headline_style", "lead_vs_related_headlines",
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tables", help="folder written by build_tables")
    ap.add_argument("out", help="where to write the JSON files (site/public/data)")
    ap.add_argument("--db", default=":memory:", help="optional DuckDB file to keep the tables")
    ap.add_argument("--no-merge", action="store_true", help="don't merge outlet names that share a website")
    a = ap.parse_args()

    t, out = Path(a.tables), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(a.db)

    con.execute("SET TimeZone = 'UTC'")  # published dates in the feeds are UTC
    con.execute("CREATE OR REPLACE TABLE editions (country VARCHAR, label VARCHAR, sort INT, tz VARCHAR)")
    con.executemany("INSERT INTO editions VALUES (?, ?, ?, ?)", EDITIONS)
    cols = con.execute(f"SELECT * FROM read_csv('{t / 'stories.csv.gz'}', all_varchar = true) LIMIT 0").description
    has_link = "link_phrase" in [c[0] for c in cols]  # older build_tables output has no link_phrase
    con.execute(f"""
        CREATE OR REPLACE TABLE stories AS
        SELECT story_id, country, topic_folder AS category, file_date::DATE AS file_date,
               rank_in_file::INT AS rank_in_file, title,
               coalesce(publisher_name, '') AS lead_outlet, publisher_website AS lead_website,
               try_cast(published_date AS TIMESTAMP) AS published_at, url, cluster_size::INT AS cluster_size,
               {"coalesce(link_phrase, '')" if has_link else "''"} AS link_phrase
        FROM read_csv('{t / "stories.csv.gz"}', all_varchar = true)""")
    con.execute(f"""
        CREATE OR REPLACE TABLE cluster_items AS
        SELECT story_id, position::INT AS position, headline, coalesce(outlet, '') AS outlet, parse
        FROM read_csv('{t / "cluster_items.csv.gz"}', all_varchar = true)""")
    con.execute(f"""
        CREATE OR REPLACE TABLE coverage AS
        SELECT country, topic AS category, date::DATE AS date, n_stories::INT AS n_stories
        FROM read_csv('{t / "coverage.csv"}', all_varchar = true)""")

    # merge outlet names that point to the same website ("Ntv" and "n-tv.de")
    if not a.no_merge:
        con.execute(ALIAS_SQL.format(shared=", ".join(f"'{d}'" for d in SHARED_DOMAINS)))
        con.execute("""UPDATE stories SET lead_outlet = a.canonical FROM outlet_alias a
                       WHERE stories.country = a.country AND stories.lead_outlet = a.outlet""")
        con.execute("""UPDATE cluster_items SET outlet = a.canonical FROM outlet_alias a
                       WHERE split_part(cluster_items.story_id, '|', 1) = a.country AND cluster_items.outlet = a.outlet""")
        n = con.execute("SELECT count(*) FROM outlet_alias").fetchone()[0]
        con.execute(f"COPY outlet_alias TO '{t / 'outlet_aliases.csv'}' (HEADER)")
        print(f"merged {n} outlet names into the main name of their website (see {t / 'outlet_aliases.csv'})")

    for name in EXPORT + LABEL_EXPORT + ["sources", "sources_by_category", "labels_review", "outlet_labels"]:
        con.execute(f"DROP TABLE IF EXISTS {name}")
    con.execute("DROP MACRO IF EXISTS headline_features")
    con.execute(SQL.read_text())

    # outlet labels and the aggregates that use them
    n = build_label_table(con)
    con.execute(LABELS_SQL.read_text())
    con.execute(f"COPY labels_review TO '{t / 'labels_review.csv'}' (HEADER)")
    print(f"labelled {n} outlets; check the top ones in {t / 'labels_review.csv'}")

    for name in EXPORT + LABEL_EXPORT:
        rel = con.execute(f"SELECT * FROM {name}")
        cols = [d[0] for d in rel.description]
        rows = [dict(zip(cols, r)) for r in rel.fetchall()]
        path = out / f"{name}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False, default=str, separators=(",", ":")))
        print(f"{path}  {len(rows)} rows")


if __name__ == "__main__":
    main()
