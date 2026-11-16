#!/usr/bin/env python3
"""
Write a small fake archive in the same format as the real daily Google News CSVs,
to test the whole pipeline without the real data.

    python tests/make_synthetic.py /tmp/fake_daily_news_csv
"""
import csv
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(7)
TOPICS = ["Business", "Health", "Nation", "Politics", "Science", "Technology", "World"]
EDITIONS = {
    "US": ("United States", [("The New York Times", "https://www.nytimes.com"), ("Reuters", "https://www.reuters.com"),
                             ("AP News", "https://apnews.com"), ("BBC", "https://www.bbc.com"), ("CNN", "https://www.cnn.com"),
                             ("Yahoo", "https://www.yahoo.com"), ("NPR", "https://www.npr.org"), ("Fox News", "https://www.foxnews.com"),
                             ("The Times of India", "https://timesofindia.indiatimes.com"), ("Al Jazeera", "https://www.aljazeera.com"),
                             ("RT", "https://www.rt.com"), ("WKYT", "https://www.wkyt.com")],
           "View Full Coverage on Google News", "See more headlines & perspectives on Google News"),
    "FR": ("France", [("Le Monde.fr", "https://www.lemonde.fr"), ("Le Figaro", "https://www.lefigaro.fr"),
                      ("franceinfo", "https://www.franceinfo.fr"), ("RFI", "https://www.rfi.fr"), ("BFM", "https://www.bfmtv.com"),
                      ("Ouest-France", "https://www.ouest-france.fr"), ("20 Minutes", "https://www.20minutes.fr"),
                      ("Euronews", "https://fr.euronews.com"), ("Le Soir", "https://www.lesoir.be")],
           "Voir la couverture complète sur Google Actualités", "Voir plus de titres et de points de vue sur Google Actualités"),
    "Germany": ("Germany", [("WELT", "https://www.welt.de"), ("Spiegel", "https://www.spiegel.de"), ("T-Online", "https://www.t-online.de"),
                            ("tagesschau.de", "https://www.tagesschau.de"), ("ZDFheute", "https://www.zdf.de"), ("BILD", "https://www.bild.de"),
                            ("n-tv.de", "https://www.n-tv.de"), ("Ntv", "https://www.n-tv.de"), ("DER STANDARD", "https://www.derstandard.at")],
                "Mehr zum Thema ansehen in Google News", "Weitere Schlagzeilen und Meinungen in Google News"),
    "Romania": ("Romania", [("Digi24", "https://www.digi24.ro"), ("HotNews.ro", "https://hotnews.ro"), ("G4Media", "https://www.g4media.ro"),
                            ("Agerpres", "https://www.agerpres.ro"), ("Libertatea", "https://www.libertatea.ro"),
                            ("Stirile ProTV", "https://stirileprotv.ro"), ("TVR Info", "https://tvrinfo.ro"), ("Sputnik Moldova", "https://md.sputniknews.ru")],
                "Vedeți vizualizarea În detaliu în Știri Google", "Vedeți mai multe titluri și perspective în Știri Google"),
}
WORDS = {
    "US": "Trump Ukraine Russia election Senate budget vaccine climate China tariffs Gaza Israel AI chips court ruling midterms Congress".split(),
    "FR": "Macron Ukraine Russie élection Assemblée budget vaccin climat Chine retraites Gaza Israël IA tribunal Barnier Sénat".split(),
    "Germany": "Merz Ukraine Russland Wahl Bundestag Haushalt Impfstoff Klima China Zölle Gaza Israel KI Gericht Koalition".split(),
    "Romania": "Nicușor Dan Ucraina Rusia alegeri Parlament buget vaccin climă China Moldova Gaza Israel AI tribunal guvern".split(),
}
SWITCH = date(2026, 6, 1)  # fake date when Google changed the link wording


def headline(country):
    w = random.sample(WORDS[country], 5)
    h = " ".join(w).capitalize()
    r = random.random()
    return h + ("?" if r < 0.1 else (f" : {random.randint(2, 90)} morts" if r < 0.2 else ""))


def main(root):
    root = Path(root)
    for ed, (_, outlets, old_link, new_link) in EDITIONS.items():
        start = date(2026, 1, 1) if ed == "US" else date(2026, 3, 13)
        weights = [len(outlets) - i for i in range(len(outlets))]
        for topic in TOPICS:
            d = root / ed / topic
            d.mkdir(parents=True, exist_ok=True)
            day = start
            while day <= date(2026, 11, 15):
                path = d / f"headlines_{day}.csv"
                if random.random() < 0.02:          # an empty file, like the real gaps
                    path.write_text("")
                    day += timedelta(days=1)
                    continue
                with open(path, "w", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["title", "description", "url", "topic", "publisher_name", "publisher_website", "published_date"])
                    for k in range(random.randint(8, 20)):
                        size = 1 if random.random() < 0.35 else random.randint(2, 5)
                        chosen = []
                        while len(chosen) < size:
                            o = random.choices(outlets, weights)[0]
                            if o not in chosen:
                                chosen.append(o)
                        heads = [headline(ed) for _ in chosen]
                        desc = heads[0] + "  " + "".join(f"{chosen[i][0]}{heads[i + 1]}  " for i in range(size - 1)) + chosen[-1][0]
                        if random.random() < 0.3:
                            desc += new_link if day >= SWITCH else old_link
                        pub = datetime(day.year, day.month, day.day, random.randint(0, 23), random.randint(0, 59)) \
                            - timedelta(days=random.choice([0, 0, 0, 1, 1, 2, 5]))
                        url = f"https://news.google.com/rss/articles/{ed}{topic}{day}{k}" if random.random() > 0.2 \
                            else f"https://news.google.com/rss/articles/{ed}{day}{k % 5}"  # some shared across topics
                        w.writerow([heads[0], desc, url, topic.upper(), chosen[0][0], chosen[0][1], pub.strftime("%Y-%m-%d %H:%M:%S")])
                day += timedelta(days=1)
    print(f"fake archive written to {root}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/fake_daily_news_csv")
