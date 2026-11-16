#!/usr/bin/env python3
"""
Headline text analyses: distinctive keywords per week, most-mentioned names, and the
countries mentioned in World news. Uses the lead headlines in stories.csv.gz.

Usage (on carrot, after build_tables):
    pip install babel stopwordsiso
    python -m gnobs.text_analyses ../out_news_tables ../site/public/data

Writes keywords_weekly.json, keywords_overall.json, names_monthly.json, names_overall.json,
country_mentions.json.
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

EDITIONS = {"US": ("United States", "en"), "FR": ("France", "fr"), "Germany": ("Germany", "de"), "Romania": ("Romania", "ro")}
TOKEN = re.compile(r"[^\W\d_][\w'’-]*", re.UNICODE)
# capitalized word sequences (2-3 words) = a cheap stand-in for person / organization names
CAP = r"[A-ZÀ-ÖØ-ÞĂÂÎȘȚŞŢ][\w.-]+"
NAME = re.compile(rf"(?<![\w'’])({CAP}(?:\s+(?:(?:de|von|van|der|la|le|del|du|da|al)\s+)*{CAP}){{1,2}})")
EXTRA_STOP = {
    "en": {"says", "said", "new", "after", "amid", "over", "how", "what", "why", "who", "will", "could", "may", "live", "updates", "news", "report"},
    "fr": {"selon", "après", "face", "nouveau", "nouvelle", "direct", "comment", "pourquoi", "quoi", "info", "infos", "vidéo"},
    "de": {"neue", "neuer", "nach", "warum", "wie", "was", "live", "ticker", "news", "video", "jetzt"},
    "ro": {"după", "noi", "nou", "nouă", "cum", "ce", "care", "video", "live", "știri", "anunță", "spune"},
}


def stopwords(lang):
    try:
        import stopwordsiso
        sw = set(stopwordsiso.stopwords(lang))
    except Exception:  # package missing: a tiny fallback list
        sw = set("the a an of to in on for and or is are with at by from as be it this that le la les de des du et un une en au aux pour par sur dans der die das und den dem des ein eine im mit von zu auf für ist si și în la de cu pe un o din".split())
    return sw | EXTRA_STOP.get(lang, set())


def tokens(title, sw):
    words = [w.lower().strip("'’-") for w in TOKEN.findall(title or "")]
    words = [w for w in words if len(w) >= 3 and w not in sw]
    return words + [f"{a} {b}" for a, b in zip(words, words[1:])]


def country_gazetteer():
    """{language: [(regex, ISO2, English name)]} from Babel's country names."""
    try:
        from babel import Locale
    except Exception:
        print("babel not installed: skipping country mentions (pip install babel)")
        return None
    en = Locale("en").territories
    out = {}
    for lang in ("en", "fr", "de", "ro"):
        names = Locale(lang).territories
        pats = []
        for iso, name in names.items():
            if not (len(iso) == 2 and iso.isalpha()) or iso in ("EU", "EZ", "UN", "QO", "XA", "XB", "ZZ"):
                continue
            variants = {name}
            if lang == "en" and iso == "US":
                variants |= {"US", "U.S.", "USA", "America"}
            if lang == "en" and iso == "GB":
                variants |= {"UK", "Britain", "U.K."}
            for v in variants:
                pats.append((re.compile(r"(?<!\w)" + re.escape(v) + r"(?!\w)", re.I if len(v) > 3 else 0), iso, en.get(iso, iso)))
        out[lang] = pats
    return out


def main(tables, out):
    tables, out = Path(tables), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    s = pd.read_csv(tables / "stories.csv.gz", dtype=str, keep_default_na=False,
                    usecols=["country", "topic_folder", "file_date", "title"])
    s["week"] = pd.to_datetime(s["file_date"]).dt.to_period("W-SUN").dt.start_time.dt.strftime("%Y-%m-%d")
    s["month"] = s["file_date"].str[:7]

    kw_week, kw_all, names_month, names_all, mentions = [], [], [], [], []
    gaz = country_gazetteer()
    for code, (label, lang) in EDITIONS.items():
        e = s[s["country"] == code]
        if e.empty:
            continue
        sw = stopwords(lang)

        # distinctive keywords per week: count in the week vs share over the whole period
        total, by_week, n_week = Counter(), defaultdict(Counter), Counter()
        for week, title in zip(e["week"], e["title"]):
            t = set(tokens(title, sw))
            total.update(t)
            by_week[week].update(t)
            n_week[week] += 1
        n_all = len(e)
        for term, n in total.most_common(30):
            kw_all.append({"country": label, "term": term, "stories": n})
        for week, c in sorted(by_week.items()):
            scored = []
            for term, n in c.items():
                if n < 5:
                    continue
                lift = (n / n_week[week]) / ((total[term] + 1) / n_all)
                scored.append((n * math.log(1 + lift), term, n, lift))
            for _, term, n, lift in sorted(scored, reverse=True)[:10]:
                kw_week.append({"country": label, "week": week, "term": term, "stories": n, "lift": round(lift, 2)})

        # names: capitalized sequences, not the first word of the headline
        nm_all, nm_month = Counter(), defaultdict(Counter)
        for month, title in zip(e["month"], e["title"]):
            found = set()
            for m in NAME.findall(title or ""):
                words = m.split()
                if any(w.lower() in sw for w in words):  # "Says It Used" and similar title-case phrases
                    continue
                found.add(re.sub(r"['’]s$", "", m))
            nm_all.update(found)
            nm_month[month].update(found)
        for name, n in nm_all.most_common(25):
            names_all.append({"country": label, "name": name, "stories": n})
        for month, c in sorted(nm_month.items()):
            for name, n in c.most_common(10):
                names_month.append({"country": label, "month": month, "name": name, "stories": n})

        # countries mentioned in World headlines
        if gaz:
            w = e[e["topic_folder"] == "World"]["title"]
            cnt = Counter()
            for title in w:
                hit = {iso: name for rx, iso, name in gaz[lang] + (gaz["en"] if lang != "en" else []) if rx.search(title or "")}
                for iso, name in hit.items():
                    cnt[(iso, name)] += 1
            for (iso, name), n in cnt.most_common(40):
                mentions.append({"country": label, "iso": iso, "mentioned": name, "stories": n,
                                 "share": round(n / max(len(w), 1), 4)})

    for name, rows in [("keywords_weekly", kw_week), ("keywords_overall", kw_all), ("names_monthly", names_month),
                       ("names_overall", names_all), ("country_mentions", mentions)]:
        (out / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
        print(f"{out / name}.json  {len(rows)} rows")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
