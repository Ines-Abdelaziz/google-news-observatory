"""
Outlet labels: country of the outlet, type, and state control.

Labels come, in order of priority, from
  1. pipeline/labels/outlet_labels.csv   (manual, edit it to correct anything)
  2. KNOWN below                          (major outlets, by domain)
  3. the website's country code           (.fr, .de, .ro, .co.uk ...) for the country only
Anything else is left 'unknown' / 'other'.

Types: public service, state-controlled, wire agency, aggregator, commercial, other.
"state-controlled" means owned or directed by a government, outside public-service
governance (e.g. RT, CGTN). Public broadcasters with independent governance are
"public service".
"""
import csv
import re
from pathlib import Path

MANUAL = Path(__file__).resolve().parents[1] / "labels" / "outlet_labels.csv"

# edition label -> ISO country code
EDITION_ISO = {"United States": "US", "France": "FR", "Germany": "DE", "Romania": "RO"}

# domain -> (country, type)
KNOWN = {
    # United States
    "nytimes.com": ("US", "commercial"), "washingtonpost.com": ("US", "commercial"), "cnn.com": ("US", "commercial"),
    "foxnews.com": ("US", "commercial"), "nbcnews.com": ("US", "commercial"), "cbsnews.com": ("US", "commercial"),
    "abcnews.go.com": ("US", "commercial"), "abcnews.com": ("US", "commercial"), "usatoday.com": ("US", "commercial"),
    "wsj.com": ("US", "commercial"), "politico.com": ("US", "commercial"), "thehill.com": ("US", "commercial"),
    "axios.com": ("US", "commercial"), "bloomberg.com": ("US", "commercial"), "cnbc.com": ("US", "commercial"),
    "latimes.com": ("US", "commercial"), "nypost.com": ("US", "commercial"), "newsweek.com": ("US", "commercial"),
    "theatlantic.com": ("US", "commercial"), "time.com": ("US", "commercial"), "forbes.com": ("US", "commercial"),
    "businessinsider.com": ("US", "commercial"), "phys.org": ("US", "commercial"), "sciencealert.com": ("AU", "commercial"),
    "space.com": ("US", "commercial"), "theverge.com": ("US", "commercial"), "techcrunch.com": ("US", "commercial"),
    "wired.com": ("US", "commercial"), "arstechnica.com": ("US", "commercial"), "engadget.com": ("US", "commercial"),
    "npr.org": ("US", "public service"), "pbs.org": ("US", "public service"), "voanews.com": ("US", "state-controlled"),
    "rferl.org": ("US", "state-controlled"), "apnews.com": ("US", "wire agency"),
    "yahoo.com": ("US", "aggregator"), "msn.com": ("US", "aggregator"), "newsbreak.com": ("US", "aggregator"),
    "ground.news": ("CA", "aggregator"),
    # United Kingdom and international
    "bbc.com": ("GB", "public service"), "bbc.co.uk": ("GB", "public service"), "theguardian.com": ("GB", "commercial"),
    "reuters.com": ("GB", "wire agency"), "ft.com": ("GB", "commercial"), "independent.co.uk": ("GB", "commercial"),
    "telegraph.co.uk": ("GB", "commercial"), "economist.com": ("GB", "commercial"), "skynews.com": ("GB", "commercial"),
    "news.sky.com": ("GB", "commercial"), "dailymail.co.uk": ("GB", "commercial"), "euronews.com": ("FR", "commercial"),
    "politico.eu": ("BE", "commercial"), "timesofindia.indiatimes.com": ("IN", "commercial"),
    "ndtv.com": ("IN", "commercial"), "hindustantimes.com": ("IN", "commercial"), "punchng.com": ("NG", "commercial"),
    "vanguardngr.com": ("NG", "commercial"),
    # France
    "lemonde.fr": ("FR", "commercial"), "lefigaro.fr": ("FR", "commercial"), "liberation.fr": ("FR", "commercial"),
    "20minutes.fr": ("FR", "commercial"), "leparisien.fr": ("FR", "commercial"), "ouest-france.fr": ("FR", "commercial"),
    "lesechos.fr": ("FR", "commercial"), "bfmtv.com": ("FR", "commercial"), "tf1info.fr": ("FR", "commercial"),
    "lci.fr": ("FR", "commercial"), "lexpress.fr": ("FR", "commercial"), "lepoint.fr": ("FR", "commercial"),
    "nouvelobs.com": ("FR", "commercial"), "huffingtonpost.fr": ("FR", "commercial"), "sudouest.fr": ("FR", "commercial"),
    "ladepeche.fr": ("FR", "commercial"), "cnews.fr": ("FR", "commercial"), "europe1.fr": ("FR", "commercial"),
    "rtl.fr": ("FR", "commercial"), "futura-sciences.com": ("FR", "commercial"), "sciencepost.fr": ("FR", "commercial"),
    "lesnumeriques.com": ("FR", "commercial"), "01net.com": ("FR", "commercial"), "numerama.com": ("FR", "commercial"),
    "franceinfo.fr": ("FR", "public service"), "francetvinfo.fr": ("FR", "public service"),
    "france24.com": ("FR", "public service"), "rfi.fr": ("FR", "public service"), "radiofrance.fr": ("FR", "public service"),
    "la1ere.francetvinfo.fr": ("FR", "public service"), "france3-regions.francetvinfo.fr": ("FR", "public service"),
    "afp.com": ("FR", "wire agency"),
    # Germany (and German-language)
    "welt.de": ("DE", "commercial"), "spiegel.de": ("DE", "commercial"), "t-online.de": ("DE", "commercial"),
    "zeit.de": ("DE", "commercial"), "fr.de": ("DE", "commercial"), "bild.de": ("DE", "commercial"),
    "merkur.de": ("DE", "commercial"), "n-tv.de": ("DE", "commercial"), "handelsblatt.com": ("DE", "commercial"),
    "tagesspiegel.de": ("DE", "commercial"), "faz.net": ("DE", "commercial"), "sueddeutsche.de": ("DE", "commercial"),
    "stern.de": ("DE", "commercial"), "focus.de": ("DE", "commercial"), "rnd.de": ("DE", "commercial"),
    "heise.de": ("DE", "commercial"), "golem.de": ("DE", "commercial"), "chip.de": ("DE", "commercial"),
    "tagesschau.de": ("DE", "public service"), "zdf.de": ("DE", "public service"), "zdfheute.de": ("DE", "public service"),
    "deutschlandfunk.de": ("DE", "public service"), "br.de": ("DE", "public service"), "ndr.de": ("DE", "public service"),
    "wdr.de": ("DE", "public service"), "mdr.de": ("DE", "public service"), "swr.de": ("DE", "public service"),
    "hr.de": ("DE", "public service"), "rbb24.de": ("DE", "public service"), "dw.com": ("DE", "public service"),
    "derstandard.at": ("AT", "commercial"), "orf.at": ("AT", "public service"), "nzz.ch": ("CH", "commercial"),
    "srf.ch": ("CH", "public service"), "dpa.com": ("DE", "wire agency"),
    # Romania
    "digi24.ro": ("RO", "commercial"), "hotnews.ro": ("RO", "commercial"), "libertatea.ro": ("RO", "commercial"),
    "g4media.ro": ("RO", "commercial"), "stirileprotv.ro": ("RO", "commercial"), "adevarul.ro": ("RO", "commercial"),
    "ziare.com": ("RO", "commercial"), "antena3.ro": ("RO", "commercial"), "profit.ro": ("RO", "commercial"),
    "mobilissimo.ro": ("RO", "commercial"), "connect.ro": ("RO", "commercial"), "romaniatv.net": ("RO", "commercial"),
    "realitatea.net": ("RO", "commercial"), "gandul.ro": ("RO", "commercial"), "observatornews.ro": ("RO", "commercial"),
    "agerpres.ro": ("RO", "wire agency"), "mediafax.ro": ("RO", "wire agency"), "news.ro": ("RO", "wire agency"),
    "tvrinfo.ro": ("RO", "public service"), "tvr.ro": ("RO", "public service"), "romania-actualitati.ro": ("RO", "public service"),
    "rri.ro": ("RO", "public service"), "radioromaniacultural.ro": ("RO", "public service"),
    # State-controlled media
    "rt.com": ("RU", "state-controlled"), "sputniknews.com": ("RU", "state-controlled"),
    "sputniknews.ru": ("RU", "state-controlled"), "tass.com": ("RU", "state-controlled"), "tass.ru": ("RU", "state-controlled"),
    "ria.ru": ("RU", "state-controlled"), "cgtn.com": ("CN", "state-controlled"), "xinhuanet.com": ("CN", "state-controlled"),
    "news.cn": ("CN", "state-controlled"), "chinadaily.com.cn": ("CN", "state-controlled"),
    "globaltimes.cn": ("CN", "state-controlled"), "trtworld.com": ("TR", "state-controlled"),
    "trthaber.com": ("TR", "state-controlled"), "aa.com.tr": ("TR", "state-controlled"),
    "presstv.ir": ("IR", "state-controlled"), "aljazeera.com": ("QA", "state-controlled"),
    "aljazeera.net": ("QA", "state-controlled"),
}

# country-code top-level domains -> country (generic ones like .com are left unknown)
CCTLD = {"fr": "FR", "de": "DE", "ro": "RO", "md": "MD", "uk": "GB", "be": "BE", "ch": "CH", "at": "AT",
         "it": "IT", "es": "ES", "pt": "PT", "nl": "NL", "pl": "PL", "hu": "HU", "bg": "BG", "ru": "RU",
         "ua": "UA", "in": "IN", "ng": "NG", "ca": "CA", "au": "AU", "ie": "IE", "lu": "LU", "ma": "MA",
         "dz": "DZ", "tn": "TN", "sn": "SN", "ci": "CI", "cm": "CM", "cn": "CN", "jp": "JP", "il": "IL",
         "tr": "TR", "gr": "GR", "cz": "CZ", "sk": "SK", "se": "SE", "dk": "DK", "no": "NO", "fi": "FI",
         "za": "ZA", "ke": "KE", "pk": "PK", "nz": "NZ", "sg": "SG", "ph": "PH", "br": "BR", "mx": "MX",
         "ar": "AR", "us": "US", "re": "FR", "nc": "FR", "pf": "FR", "mg": "MG", "ir": "IR", "qa": "QA"}

NAME_TYPES = [  # fallback by outlet name
    (re.compile(r"\b(yahoo|msn|newsbreak|ground news)\b", re.I), "aggregator"),
    (re.compile(r"^(ap news|associated press|reuters|afp|agence france-presse|dpa|agerpres|mediafax)\b", re.I), "wire agency"),
]


def domain_of(website: str, outlet: str = "") -> str:
    """'https://www.lemonde.fr/...' -> 'lemonde.fr'. Falls back to a domain-like outlet name ('HotNews.ro')."""
    w = (website or "").strip().lower()
    if not w and re.fullmatch(r"[\w.-]+\.[a-z]{2,}", (outlet or "").strip().lower()):
        w = outlet.strip().lower()
    w = re.sub(r"^[a-z]+://", "", w).split("/")[0]
    return re.sub(r"^(www\d?|m|amp)\.", "", w)


def known_for(domain: str):
    """Match a domain or any of its parents in KNOWN (fr.euronews.com -> euronews.com)."""
    parts = domain.split(".")
    for i in range(len(parts) - 1):
        d = ".".join(parts[i:])
        if d in KNOWN:
            return KNOWN[d]
    return None


def load_manual():
    if not MANUAL.exists():
        return {}
    with open(MANUAL, newline="") as f:
        return {(r.get("outlet") or "").strip(): r for r in csv.DictReader(f) if not r.get("outlet", "").startswith("#")}


def label(outlet: str, website: str, manual: dict):
    dom = domain_of(website, outlet)
    country, otype = "unknown", "other"
    k = known_for(dom) if dom else None
    if k:
        country, otype = k
    elif dom:
        tld = dom.rsplit(".", 1)[-1]
        country = CCTLD.get(tld, "unknown")
    for rx, t in NAME_TYPES:
        if otype == "other" and rx.search(outlet or ""):
            otype = t
    m = manual.get(outlet)
    if m:
        country = (m.get("outlet_country") or country).strip() or country
        otype = (m.get("outlet_type") or otype).strip() or otype
    return dom, country, otype


def build_label_table(con):
    """Create table outlet_labels(country, outlet, domain, outlet_country, outlet_type, origin)."""
    manual = load_manual()
    rows = con.execute("SELECT country, outlet, coalesce(website, '') FROM sources").fetchall()
    out = []
    for edition, outlet, website in rows:
        dom, oc, ot = label(outlet, website, manual)
        origin = "unknown" if oc == "unknown" else ("domestic" if oc == EDITION_ISO.get(edition) else "foreign")
        out.append((edition, outlet, dom, oc, ot, origin))
    con.execute("""CREATE OR REPLACE TABLE outlet_labels (country VARCHAR, outlet VARCHAR, domain VARCHAR,
                   outlet_country VARCHAR, outlet_type VARCHAR, origin VARCHAR)""")
    con.executemany("INSERT INTO outlet_labels VALUES (?, ?, ?, ?, ?, ?)", out)
    return len(out)
