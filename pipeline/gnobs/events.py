#!/usr/bin/env python3
"""
Match the same news event across the four editions (World and Politics lead headlines),
using a multilingual sentence-embedding model.

Usage (on carrot, after build_tables; a GPU helps but is not required):
    pip install sentence-transformers
    python -m gnobs.events ../out_news_tables ../site/public/data

Method: two headlines from different editions are the same event if they are each other's
most similar headline (cosine >= --threshold) within a +/-1 day window. Linked headlines are
grouped into events (connected components).

Writes:
  event_coverage.json     per edition: share of its stories whose event is covered by 1, 2, 3 or 4 editions
  shared_events.json      the events covered by the most editions, with each edition's lead headline and outlet
  event_lead_origin.json  for events covered by 2+ editions: is the same outlet credited in several editions?
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

EDITIONS = {"US": "United States", "FR": "France", "Germany": "Germany", "Romania": "Romania"}
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def embed(titles, model_name):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    return model.encode(titles, batch_size=256, show_progress_bar=True, normalize_embeddings=True)


class UnionFind:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def link_events(df, vecs, threshold):
    """Return a component id per row of df (columns: country, day)."""
    uf = UnionFind(len(df))
    idx = defaultdict(list)  # (country, day) -> row numbers
    for i, (c, d) in enumerate(zip(df["country"], df["day"])):
        idx[(c, d)].append(i)
    days = sorted(df["day"].unique())
    eds = list(EDITIONS)
    for d in days:
        for ai, a in enumerate(eds):
            A = idx.get((a, d), [])
            if not A:
                continue
            for b in eds[ai + 1:]:
                B = [j for dd in (d - 1, d, d + 1) for j in idx.get((b, dd), [])]
                if not B:
                    continue
                sim = vecs[A] @ vecs[B].T
                best_b = sim.argmax(axis=1)
                best_a = sim.argmax(axis=0)
                for x, y in enumerate(best_b):
                    if best_a[y] == x and sim[x, y] >= threshold:
                        uf.union(A[x], B[y])
    return [uf.find(i) for i in range(len(df))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tables")
    ap.add_argument("out")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--categories", default="World,Politics")
    a = ap.parse_args(args=None)
    run(a.tables, a.out, a.model, a.threshold, a.categories.split(","))


def run(tables, out, model, threshold, categories, embedder=None):
    tables, out = Path(tables), Path(out)
    s = pd.read_csv(tables / "stories.csv.gz", dtype=str, keep_default_na=False,
                    usecols=["country", "topic_folder", "file_date", "title", "publisher_name", "url"])
    s = s[s["topic_folder"].isin(categories) & (s["title"] != "")]
    # one row per lead article per edition and day (the same story can be in two sections)
    s = s.drop_duplicates(["country", "file_date", "url"]).reset_index(drop=True)
    s["day"] = (pd.to_datetime(s["file_date"]) - pd.Timestamp("2026-01-01")).dt.days
    print(f"{len(s)} headlines to embed")
    vecs = (embedder or (lambda t: embed(t, model)))(s["title"].tolist())
    vecs = np.asarray(vecs, dtype=np.float32)
    s["event"] = link_events(s, vecs, threshold)

    ev = s.groupby("event").agg(editions=("country", "nunique"), stories=("country", "size"),
                                first_day=("file_date", "min")).reset_index()
    s = s.merge(ev[["event", "editions"]], on="event")

    cov = (s.groupby(["country", "editions"]).size().rename("stories").reset_index())
    cov["share"] = (cov["stories"] / cov.groupby("country")["stories"].transform("sum")).round(4)
    cov["country"] = cov["country"].map(EDITIONS)

    top = ev[ev["editions"] >= 3].sort_values(["editions", "stories"], ascending=False).head(60)
    shared = []
    for _, e in top.iterrows():
        rows = s[s["event"] == e["event"]]
        per = {}
        for c, g in rows.groupby("country"):
            r = g.iloc[0]
            per[EDITIONS[c]] = {"headline": r["title"], "outlet": r["publisher_name"], "date": r["file_date"]}
        shared.append({"event": int(e["event"]), "editions": int(e["editions"]), "stories": int(e["stories"]),
                       "first_date": e["first_day"], "by_edition": per})

    # events covered by 2+ editions: is the same outlet credited in several editions?
    multi = s[s["editions"] >= 2]
    origin = []
    for eid, g in multi.groupby("event"):
        lead = g.groupby("country")["publisher_name"].agg(lambda x: x.value_counts().index[0])
        counts = lead.value_counts()
        origin.append({"event": int(eid), "editions": int(lead.size), "distinct_lead_outlets": int(lead.nunique()),
                       "shared_lead_outlet": counts.index[0] if counts.iloc[0] >= 2 else None})

    out.mkdir(parents=True, exist_ok=True)
    for name, rows in [("event_coverage", cov.to_dict("records")), ("shared_events", shared),
                       ("event_lead_origin", origin)]:
        (out / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, default=int, separators=(",", ":")))
        print(f"{out / name}.json  {len(rows)} rows")


if __name__ == "__main__":
    main()
