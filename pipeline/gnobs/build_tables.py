#!/usr/bin/env python3
"""
Build analysis tables from the daily Google News CSVs.

Usage (from the videos_discoveryy folder):
    python -m gnobs.build_tables ../../data/daily_news_csv ../out_news_tables

Reads only: countries FR, Germany, Romania, US
            topics Business, Health, Nation, Politics, Science, Technology, World
            files headlines_2026-*.csv
(Global and archive are skipped.)

Writes, in <out>/ (full tables, keep on the server):
    stories.csv.gz        one row per story (the lead article)
    cluster_items.csv.gz  one row per article in each story's cluster (position 0 = lead)
    sources.csv.gz        one row per outlet x country: leads, appearances, lead rate
    coverage.csv          rows per country x topic x day (to spot missing days)
    parse_report.txt      how well the clusters were parsed
and in <out>/share/ (small result tables, the only thing to send):
    sources.csv.gz, sources_by_topic.csv.gz, concentration_monthly.csv,
    top_outlets_monthly.csv, cluster_sizes.csv, coverage.csv, parse_report.txt
"""
import os
import re
import sys
from collections import defaultdict

import pandas as pd

COUNTRIES = ["FR", "Germany", "Romania", "US"]
TOPICS = ["Business", "Health", "Nation", "Politics", "Science", "Technology", "World"]
FILE_RE = re.compile(r"^headlines_(2026-\d{2}-\d{2})\.csv$")
# Google News separates headline and outlet with two (non-breaking) spaces
SEP_RE = re.compile(r"(?:[ \t]|\xa0){2,}")
TAILS = defaultdict(int)  # trailing "full coverage" phrases found, for the report


def list_files(root):
    for country in COUNTRIES:
        for topic in TOPICS:
            d = os.path.join(root, country, topic)
            if not os.path.isdir(d):
                print(f"[warn] missing folder {d}")
                continue
            for name in sorted(os.listdir(d)):
                m = FILE_RE.match(name)
                if m:
                    yield country, topic, m.group(1), os.path.join(d, name)


def read_csv(path):
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception as e:  # empty or malformed file
        print(f"[warn] cannot read {path}: {e}")
        return None
    return df


def split_parts(desc):
    return [p.strip() for p in SEP_RE.split(str(desc).strip()) if p.strip()]


def heuristic_split(mid):
    """Fallback for an unknown outlet glued to a headline, e.g. 'CNNWhat is...',
    'Louisville Public MediaMcConnell...': cut at the first capital (or digit)
    that directly follows a non-space character and starts a word."""
    for i in range(1, len(mid) - 1):
        prev, c, nxt = mid[i - 1], mid[i], mid[i + 1]
        if prev == " ":
            continue
        if c.isupper() and (nxt.islower() or nxt in " '’."):
            return mid[:i].strip(), mid[i:].strip()
        if c.isdigit() and prev.isalpha():
            return mid[:i].strip(), mid[i:].strip()
    return None


def match_known(mid, known, lengths):
    """Longest known outlet name that starts `mid` (dict lookups, not a scan)."""
    for L in lengths:
        if L <= len(mid) and mid[:L] in known:
            return mid[:L]
    return None


def parse_cluster(desc, known, lengths):
    """Return list of (headline, outlet, how) from a Google News cluster string.

    The string looks like: 'H1  O1H2  O2H3  O3'. After splitting on the double
    space we get ['H1', 'O1H2', 'O2H3', 'O3']; each middle part is an outlet name
    glued to the next headline. We cut it with the longest known outlet name
    ('known'), else with a capital-letter heuristic ('heuristic'), else 'failed'.
    """
    parts = split_parts(desc)
    if not parts:
        return []
    if len(parts) == 1:  # no outlet at all
        return [(parts[0], "", "failed")]
    items = []
    headline = parts[0]
    for mid in parts[1:-1]:
        outlet = match_known(mid, known, lengths)
        if outlet is not None:
            items.append((headline, outlet, "known"))
            headline = mid[len(outlet):].strip()
            continue
        cut = heuristic_split(mid)
        if cut:
            items.append((headline, cut[0], "heuristic"))
            headline = cut[1]
        else:
            items.append((headline, "", "failed"))
            headline = mid
    last = parts[-1]
    if "Google" in last:
        # a "View Full Coverage on Google News" link is glued to the last outlet,
        # e.g. 'RFIVoir la couverture complète sur Google Actualités'
        outlet = match_known(last, known, lengths)
        if outlet:
            items.append((headline, outlet, "known"))
        else:
            cut = heuristic_split(last)
            items.append((headline, cut[0], "heuristic") if cut else (headline, "", "failed"))
        TAILS[last[len(items[-1][1]):].strip()] += 1
    else:
        items.append((headline, last, "known"))
    return items


def main(root, out):
    os.makedirs(out, exist_ok=True)
    files = list(list_files(root))
    print(f"{len(files)} files found")

    # ---- pass 1: load everything and learn outlet names -------------------
    frames, coverage = [], []
    for country, topic, day, path in files:
        df = read_csv(path)
        n = 0 if df is None else len(df)
        coverage.append({"country": country, "topic": topic, "date": day, "n_stories": n})
        if not n:
            continue
        df = df.copy()
        df["country"], df["topic_folder"], df["file_date"] = country, topic, day
        df["rank_in_file"] = range(len(df))  # row order, possibly feed order
        frames.append(df)
    stories = pd.concat(frames, ignore_index=True)
    pd.DataFrame(coverage).to_csv(os.path.join(out, "coverage.csv"), index=False)

    known = set(stories["publisher_name"].str.strip()) - {""}
    for d in stories["description"]:
        parts = split_parts(d)
        if len(parts) >= 2 and "Google" not in parts[-1]:
            known.add(parts[-1])  # the last part is a bare outlet name (unless a Google link is glued on)
    lengths = sorted({len(n) for n in known}, reverse=True)
    print(f"{len(stories)} stories, {len(known)} outlet names learned")

    # ---- pass 2: parse clusters ------------------------------------------
    stories["story_id"] = (stories["country"] + "|" + stories["topic_folder"] + "|"
                           + stories["file_date"] + "|" + stories["rank_in_file"].astype(str))
    rows, how_counts, checks = [], defaultdict(int), defaultdict(int)
    for k, (sid, title, pub, desc) in enumerate(zip(stories["story_id"], stories["title"],
                                     stories["publisher_name"], stories["description"])):
        if k % 50000 == 0:
            print(f"  parsed {k}/{len(stories)} stories", flush=True)
        items = parse_cluster(desc, known, lengths)
        checks["title_is_first"] += bool(items) and str(desc).strip().startswith(str(title).strip())
        checks["lead_outlet_matches"] += bool(items) and items[0][1] == str(pub).strip()
        for pos, (h, o, how) in enumerate(items):
            rows.append({"story_id": sid, "position": pos, "headline": h, "outlet": o, "parse": how})
            how_counts[how] += 1
    items = pd.DataFrame(rows)
    stories["cluster_size"] = stories["story_id"].map(items.groupby("story_id").size()).fillna(0).astype(int)

    keep = ["story_id", "country", "topic_folder", "topic", "file_date", "rank_in_file", "title",
            "publisher_name", "publisher_website", "published_date", "url", "cluster_size"]
    stories[[c for c in keep if c in stories.columns]].to_csv(
        os.path.join(out, "stories.csv.gz"), index=False, compression="gzip")
    items.to_csv(os.path.join(out, "cluster_items.csv.gz"), index=False, compression="gzip")

    # ---- sources table ----------------------------------------------------
    it = items[items["outlet"] != ""].merge(
        stories[["story_id", "country", "topic_folder", "file_date"]], on="story_id")
    g = it.groupby(["country", "outlet"])
    src = pd.DataFrame({
        "appearances": g.size(),
        "leads": g["position"].apply(lambda p: (p == 0).sum()),
        "n_topics": g["topic_folder"].nunique(),
        "first_seen": g["file_date"].min(),
        "last_seen": g["file_date"].max(),
    }).reset_index()
    src["lead_rate"] = (src["leads"] / src["appearances"]).round(4)
    web = (stories.groupby(["country", "publisher_name"])["publisher_website"]
           .agg(lambda s: s.mode().iat[0] if len(s.mode()) else "")
           .rename_axis(["country", "outlet"]).rename("website"))
    src = src.merge(web.reset_index(), on=["country", "outlet"], how="left")
    src.sort_values(["country", "leads"], ascending=[True, False]).to_csv(
        os.path.join(out, "sources.csv.gz"), index=False, compression="gzip")

    # ---- small result tables to share (raw data stays on the server) ------
    share = os.path.join(out, "share")
    os.makedirs(share, exist_ok=True)
    it["month"] = it["file_date"].str[:7]
    it["is_lead"] = (it["position"] == 0).astype(int)

    # per outlet x country x topic: leads and appearances
    by_topic = (it.groupby(["country", "topic_folder", "outlet"])
                .agg(appearances=("is_lead", "size"), leads=("is_lead", "sum")).reset_index())
    by_topic.to_csv(os.path.join(share, "sources_by_topic.csv.gz"), index=False, compression="gzip")
    src.to_csv(os.path.join(share, "sources.csv.gz"), index=False, compression="gzip")

    # concentration of the lead slot per country x month x topic (and all topics)
    both = pd.concat([it, it.assign(topic_folder="All")], ignore_index=True)
    leads = both[both["is_lead"] == 1]
    conc_rows = []
    for (c, m, t), grp in leads.groupby(["country", "month", "topic_folder"]):
        counts = grp["outlet"].value_counts()
        s = counts / counts.sum()
        srt = s.sort_values().values
        n = len(srt)
        gini = (2 * sum((i + 1) * v for i, v in enumerate(srt)) / (n * srt.sum()) - (n + 1) / n) if n else 0
        conc_rows.append({"country": c, "month": m, "topic": t, "stories": int(counts.sum()),
                          "lead_outlets": n, "top1_share": round(s.iloc[0], 4),
                          "top5_share": round(s.iloc[:5].sum(), 4), "top10_share": round(s.iloc[:10].sum(), 4),
                          "hhi": round((s ** 2).sum(), 5), "gini": round(gini, 4)})
    pd.DataFrame(conc_rows).to_csv(os.path.join(share, "concentration_monthly.csv"), index=False)

    # monthly leads for each country's top 30 lead outlets (others grouped)
    top = (src.sort_values("leads", ascending=False).groupby("country").head(30)[["country", "outlet"]])
    top["keep"] = True
    m = both.merge(top, on=["country", "outlet"], how="left")
    m.loc[m["keep"] != True, "outlet"] = "Other"
    monthly = (m.groupby(["country", "month", "topic_folder", "outlet"])
               .agg(appearances=("is_lead", "size"), leads=("is_lead", "sum")).reset_index())
    monthly.to_csv(os.path.join(share, "top_outlets_monthly.csv"), index=False)

    # cluster sizes and coverage
    stories.groupby(["country", "topic_folder", "cluster_size"]).size().rename("stories") \
        .reset_index().to_csv(os.path.join(share, "cluster_sizes.csv"), index=False)
    pd.DataFrame(coverage).to_csv(os.path.join(share, "coverage.csv"), index=False)

    # ---- report -----------------------------------------------------------
    n = len(stories)
    with open(os.path.join(out, "parse_report.txt"), "w") as f:
        f.write(f"files: {len(files)}\nstories: {n}\ncluster items: {len(items)}\n")
        f.write(f"outlet names learned: {len(known)}\n")
        for how in ("known", "heuristic", "failed"):
            f.write(f"items parsed '{how}': {how_counts[how]} ({how_counts[how] / max(len(items), 1):.1%})\n")
        f.write(f"description starts with title: {checks['title_is_first'] / n:.1%}\n")
        f.write(f"first cluster outlet == publisher_name: {checks['lead_outlet_matches'] / n:.1%}\n")
        f.write(f"date range: {stories['file_date'].min()} to {stories['file_date'].max()}\n")
        f.write("trailing Google links removed (most common):\n")
        for tail, cnt in sorted(TAILS.items(), key=lambda x: -x[1])[:10]:
            f.write(f"  {cnt:>7}  {tail}\n")
    import shutil
    shutil.copy(os.path.join(out, "parse_report.txt"), share)
    print(open(os.path.join(out, "parse_report.txt")).read())
    print(f"done -> {out}/")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
