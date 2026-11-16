"""
Outlet labels: where the outlet is based, what kind of outlet it is, and (where a source
exists) its political leaning. Every label records where it came from.

COUNTRY (outlet_country, country_source), first match wins:
  manual     pipeline/labels/outlet_labels.csv
  known      the KNOWN list below (by website domain)
  domain     the website's country-code domain (.fr, .de, .ro, .co.uk, ...)
  us-news    a generic domain (.com/.org/...) listed as a US news site in the domain lists
             aggregated by Robertson et al. (github.com/gitronald/domains)
  edition    a generic domain seen only in the French, German or Romanian edition:
             assumed to be based in that country (language-specific editions)
  unknown    none of the above

TYPE (outlet_type, type_source):
  public service    public broadcasters with independent governance (BBC, franceinfo, ARD/ZDF, TVR ...)
  state-controlled  owned or directed by a government outside public-service governance (RT, CGTN, Xinhua ...)
  wire agency       news agencies (AP, Reuters, AFP, dpa, Agerpres ...)
  aggregator        sites republishing other outlets (Yahoo, MSN, AOL ...)
  official          governments and institutions (elysee.fr, IMF, press-release services ...)
  private           everything else: privately owned outlets (manual/known, or 'default' when unchecked)

LEANING (leaning, leaning_source): left, lean left, center, lean right, right, unknown
  manual     pipeline/labels/outlet_labels.csv (use this for French, German and Romanian outlets,
             and say where the rating comes from in leaning_source)
  allsides   AllSides Media Bias Ratings (2018), as included in Robertson et al. (2018)
  audience   partisan audience score of Robertson et al. (2018): share of Republicans vs Democrats
             sharing the domain on Twitter, -1 (left) to +1 (right); bucketed at +-0.2 and +-0.5
  unknown    none of the above
  The AllSides and audience ratings describe US politics, so they are applied in the US edition only.
"""
import csv
import re
import urllib.request
from pathlib import Path

LABEL_DIR = Path(__file__).resolve().parents[1] / "labels"
MANUAL = LABEL_DIR / "outlet_labels.csv"
EXTERNAL = LABEL_DIR / "external"
DOMAINS_URL = "https://raw.githubusercontent.com/gitronald/domains/master/data/domains.tsv"

EDITION_ISO = {"United States": "US", "France": "FR", "Germany": "DE", "Romania": "RO"}
ALLSIDES = {-1.0: "left", -0.5: "lean left", 0.0: "center", 0.5: "lean right", 1.0: "right"}

P, S, W, A, O, C = "public service", "state-controlled", "wire agency", "aggregator", "official", "private"

# domain -> (country, type)
KNOWN = {
    # United States
    **{d: ("US", C) for d in """nytimes.com washingtonpost.com cnn.com foxnews.com foxbusiness.com nbcnews.com cbsnews.com
        abcnews.go.com abcnews.com usatoday.com wsj.com politico.com thehill.com axios.com bloomberg.com cnbc.com
        latimes.com nypost.com newsweek.com theatlantic.com time.com forbes.com fortune.com businessinsider.com
        phys.org medicalxpress.com space.com theverge.com techcrunch.com wired.com arstechnica.com engadget.com
        gizmodo.com kotaku.com ign.com gamespot.com gameinformer.com cnet.com zdnet.com tomsguide.com 9to5mac.com
        9to5google.com macrumors.com androidauthority.com androidpolice.com windowscentral.com bgr.com mashable.com
        huffpost.com thedailybeast.com slate.com buzzfeed.com dailykos.com newser.com newsnationnow.com
        marketwatch.com barrons.com investors.com fool.com thestreet.com tipranks.com inc.com seattletimes.com
        sfgate.com sfchronicle.com oregonlive.com al.com ksl.com abc7.com ktla.com komonews.com gothamist.com
        texastribune.org statnews.com scitechdaily.com sciencedaily.com livescience.com dailygalaxy.com
        spacedaily.com earth.com futurism.com iflscience.com psypost.org neurosciencenews.com spacenews.com
        eatingwell.com bleepingcomputer.com thehackernews.com wccftech.com videocardz.com techpowerup.com
        phonearena.com petapixel.com nintendolife.com pushsquare.com purexbox.com nintendoeverything.com
        gematsu.com understandingwar.org dailywire.com breitbart.com msnbc.com ms.now motherjones.com
        nationalreview.com washingtonexaminer.com theintercept.com propublica.org vox.com""".split()},
    "npr.org": ("US", P), "pbs.org": ("US", P), "voanews.com": ("US", S), "rferl.org": ("US", S),
    "apnews.com": ("US", W), "yahoo.com": ("US", A), "msn.com": ("US", A), "aol.com": ("US", A),
    "newsbreak.com": ("US", A), "ground.news": ("CA", A), "news.xbox.com": ("US", O),
    "sciencealert.com": ("AU", C), "theconversation.com": ("AU", C),
    # United Kingdom and international
    "bbc.com": ("GB", P), "bbc.co.uk": ("GB", P), "discoverwildlife.com": ("GB", C), "theguardian.com": ("GB", C),
    "reuters.com": ("GB", W), "ft.com": ("GB", C), "independent.co.uk": ("GB", C), "telegraph.co.uk": ("GB", C),
    "economist.com": ("GB", C), "skynews.com": ("GB", C), "news.sky.com": ("GB", C), "dailymail.co.uk": ("GB", C),
    "nature.com": ("GB", C), "theregister.com": ("GB", C), "eurogamer.net": ("GB", C), "newscientist.com": ("GB", C),
    "euronews.com": ("FR", C), "politico.eu": ("BE", C), "euractiv.com": ("BE", C), "euractiv.fr": ("BE", C),
    "euractiv.de": ("BE", C), "timesofindia.indiatimes.com": ("IN", C), "ndtv.com": ("IN", C),
    "hindustantimes.com": ("IN", C), "thehindu.com": ("IN", C), "indiandefencereview.com": ("IN", C),
    "punchng.com": ("NG", C), "vanguardngr.com": ("NG", C), "ghanaweb.com": ("GH", C),
    "timesofisrael.com": ("IL", C), "jpost.com": ("IL", C), "ynetnews.com": ("IL", C), "i24news.tv": ("IL", C),
    "scmp.com": ("HK", C), "kyivindependent.com": ("UA", C), "kyivpost.com": ("UA", C),
    "cbc.ca": ("CA", P), "radio-canada.ca": ("CA", P), "abc.net.au": ("AU", P), "vaticannews.va": ("VA", S),
    "imf.org": ("US", O), "lorientlejour.com": ("LB", C), "tsa-algerie.com": ("DZ", C), "koaci.com": ("CI", C),
    "fr.apanews.net": ("SN", W), "information.tv5monde.com": ("FR", P), "tv5monde.com": ("FR", P),
    "rts.ch": ("CH", P), "srf.ch": ("CH", P), "letemps.ch": ("CH", C), "lesoir.be": ("BE", C), "lalibre.be": ("BE", C),
    "rtbf.be": ("BE", P), "lapresse.ca": ("CA", C), "lessentiel.lu": ("LU", C), "20min.ch": ("CH", C), "blick.ch": ("CH", C),
    "vietnam.vn": ("VN", S),
    # France
    **{d: ("FR", C) for d in """lemonde.fr lefigaro.fr liberation.fr 20minutes.fr leparisien.fr ouest-france.fr lesechos.fr
        bfmtv.com tf1info.fr lci.fr lexpress.fr lepoint.fr nouvelobs.com huffingtonpost.fr sudouest.fr ladepeche.fr
        cnews.fr europe1.fr rtl.fr futura-sciences.com sciencepost.fr lesnumeriques.com 01net.com numerama.com
        frandroid.com clubic.com presse-citron.net journaldugeek.com korben.info boursorama.com tradingsat.com
        science-et-vie.com midilibre.fr actu.fr slate.fr actu.orange.fr nicematin.com letelegramme.fr lindependant.fr
        reporterre.net parismatch.com mediapart.fr usinenouvelle.com geo.fr laprovence.com linternaute.com
        la-croix.com charentelibre.fr zdnet.fr leprogres.fr caradisiac.com ledauphine.com jeuxvideo.com
        larepubliquedespyrenees.fr courrierinternational.com humanite.fr opex360.com latribune.fr lamontagne.fr
        lavoixdunord.fr corsematin.com atlantico.fr bvoltaire.fr lejdd.fr valeursactuelles.com marianne.net
        challenges.fr capital.fr lanouvellerepublique.fr legrandcontinent.eu""".split()},
    **{d: ("FR", P) for d in """franceinfo.fr francetvinfo.fr france24.com rfi.fr radiofrance.fr la1ere.francetvinfo.fr
        france3-regions.francetvinfo.fr francebleu.fr ici.fr franceculture.fr franceinter.fr arte.tv""".split()},
    "afp.com": ("FR", W), "elysee.fr": ("FR", O), "gouvernement.fr": ("FR", O), "service-public.fr": ("FR", O),
    # Germany (and German-language)
    **{d: ("DE", C) for d in """welt.de spiegel.de t-online.de zeit.de fr.de bild.de merkur.de n-tv.de handelsblatt.com
        tagesspiegel.de faz.net sueddeutsche.de stern.de focus.de rnd.de heise.de golem.de chip.de ad-hoc-news.de
        tag24.de taz.de spektrum.de computerbase.de morgenpost.de finanzen.net berliner-zeitung.de t3n.de wiwo.de
        rp-online.de abendblatt.de deraktionaer.de giga.de gamestar.de scinexx.de augsburger-allgemeine.de
        bz-berlin.de wallstreet-online.de tichyseinblick.de telepolis.de hna.de winfuture.de pcwelt.de rtl.de
        noz.de saarbruecker-zeitung.de businessinsider.de schwaebische.de lto.de pcgameshardware.de tz.de
        ksta.de watson.de waz.de mopo.de jungefreiheit.de saechsische.de stuttgarter-zeitung.de express.de
        nordkurier.de handelsblatt.de cicero.de nius.de apollo-news.net derstandard.de""".split()},
    "web.de": ("DE", A), "presseportal.de": ("DE", O), "idw-online.de": ("DE", O), "aerzteblatt.de": ("DE", C),
    **{d: ("DE", P) for d in """tagesschau.de zdf.de zdfheute.de deutschlandfunk.de br.de ndr.de wdr.de mdr.de swr.de
        hr.de hessenschau.de rbb24.de sr.de radiobremen.de dw.com sportschau.de""".split()},
    "derstandard.at": ("AT", C), "orf.at": ("AT", P), "nzz.ch": ("CH", C), "dpa.com": ("DE", W),
    "ukrinform.de": ("UA", S), "ukrinform.net": ("UA", S),
    # Romania and Moldova
    **{d: ("RO", C) for d in """digi24.ro hotnews.ro libertatea.ro g4media.ro stirileprotv.ro adevarul.ro ziare.com antena3.ro
        profit.ro mobilissimo.ro connect.ro romaniatv.net realitatea.net gandul.ro observatornews.ro zf.ro
        newsweek.ro spotmedia.ro jurnalul.ro economica.net gsp.ro bursa.ro digisport.ro prosport.ro economedia.ro
        republica.ro cotidianul.ro raportuldegarda.ro defenseromania.ro protv.ro forbes.ro euronews.ro europafm.ro
        biziday.ro pressone.ro recorder.ro libertatea.ro stiripesurse.ro dcnews.ro evz.ro b1tv.ro b1.ro""".split()},
    **{d: ("RO", P) for d in """tvrinfo.ro tvr.ro romania-actualitati.ro rri.ro radioromaniacultural.ro radioromania.ro
        radiocluj.ro radiooltenia.ro""".split()},
    **{d: ("RO", W) for d in "agerpres.ro mediafax.ro news.ro rador.ro".split()},
    "moldova1.md": ("MD", P), "radiomoldova.md": ("MD", P), "tv8.md": ("MD", C), "noi.md": ("MD", C),
    # State-controlled media
    **{d: ("RU", S) for d in "rt.com sputniknews.com sputniknews.ru tass.com tass.ru ria.ru".split()},
    **{d: ("CN", S) for d in "cgtn.com xinhuanet.com news.cn chinadaily.com.cn globaltimes.cn people.cn".split()},
    **{d: ("TR", S) for d in "trtworld.com trthaber.com aa.com.tr".split()},
    "presstv.ir": ("IR", S), "aljazeera.com": ("QA", S), "aljazeera.net": ("QA", S),
}

CCTLD = {"fr": "FR", "de": "DE", "ro": "RO", "md": "MD", "uk": "GB", "be": "BE", "ch": "CH", "at": "AT",
         "it": "IT", "es": "ES", "pt": "PT", "nl": "NL", "pl": "PL", "hu": "HU", "bg": "BG", "ru": "RU",
         "ua": "UA", "in": "IN", "ng": "NG", "ca": "CA", "au": "AU", "ie": "IE", "lu": "LU", "ma": "MA",
         "dz": "DZ", "tn": "TN", "sn": "SN", "ci": "CI", "cm": "CM", "cn": "CN", "jp": "JP", "il": "IL",
         "tr": "TR", "gr": "GR", "cz": "CZ", "sk": "SK", "se": "SE", "dk": "DK", "no": "NO", "fi": "FI",
         "za": "ZA", "ke": "KE", "pk": "PK", "nz": "NZ", "sg": "SG", "ph": "PH", "br": "BR", "mx": "MX",
         "ar": "AR", "us": "US", "re": "FR", "nc": "FR", "pf": "FR", "mg": "MG", "ir": "IR", "qa": "QA",
         "vn": "VN", "hk": "HK", "gh": "GH", "lb": "LB", "va": "VA", "rs": "RS", "hr": "HR", "si": "SI"}
GENERIC = {"com", "org", "net", "info", "news", "eu", "io", "tv", "co", "biz", "media", "online", "site"}
NAME_TYPES = [
    (re.compile(r"\b(yahoo|msn|aol|newsbreak|ground news)\b", re.I), A),
    (re.compile(r"^(ap news|associated press|reuters|afp|agence france-presse|dpa|agerpres|mediafax)\b", re.I), W),
]


def domain_of(website: str, outlet: str = "") -> str:
    """'https://www.lemonde.fr/...' -> 'lemonde.fr'. Falls back to a domain-like outlet name ('HotNews.ro')."""
    w = (website or "").strip().lower()
    if not w and re.fullmatch(r"[\w.-]+\.[a-z]{2,}", (outlet or "").strip().lower()):
        w = outlet.strip().lower()
    w = re.sub(r"^[a-z]+://", "", w).split("/")[0]
    return re.sub(r"^(www\d?|m|amp)\.", "", w)


def parents(domain: str):
    parts = domain.split(".")
    return [".".join(parts[i:]) for i in range(len(parts) - 1)]


def lookup(table: dict, domain: str):
    for d in parents(domain):
        if d in table:
            return table[d]
    return None


def load_manual():
    if not MANUAL.exists():
        return {}
    with open(MANUAL, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("outlet") and not r["outlet"].startswith("#")]
    return {r["outlet"].strip(): r for r in rows}


def load_us_domains():
    """{domain: (is_news, audience_score, allsides_score)} from Robertson et al.'s aggregated lists."""
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    path = EXTERNAL / "domains.tsv"
    if not path.exists():
        try:
            urllib.request.urlretrieve(DOMAINS_URL, path)
            print(f"downloaded {DOMAINS_URL}")
        except Exception as e:  # offline: no US news list and no leaning scores
            print(f"could not download the domain lists ({e}); skipping US-news and leaning labels")
            return {}
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            def num(k):
                try:
                    return float(r[k]) if r.get(k) not in (None, "") else None
                except ValueError:
                    return None
            out[r["domain"].lower()] = (num("news_is_news") == 1.0, num("bias_score"), num("bias_allsides_score"))
    return out


def bucket(score):
    if score is None:
        return None
    if score <= -0.5:
        return "left"
    if score <= -0.2:
        return "lean left"
    if score < 0.2:
        return "center"
    if score < 0.5:
        return "lean right"
    return "right"


def build_label_table(con):
    """Create table outlet_labels with country, type and leaning (and their sources) for every outlet."""
    manual, us = load_manual(), load_us_domains()
    rows = con.execute("SELECT country, outlet, coalesce(website, '') FROM sources").fetchall()
    editions_of = defaultdict_set(rows)
    out = []
    for edition, outlet, website in rows:
        dom = domain_of(website, outlet)
        tld = dom.rsplit(".", 1)[-1] if dom else ""
        known = lookup(KNOWN, dom) if dom else None
        usd = lookup(us, dom) if dom else None

        # country
        if known:
            oc, ocs = known[0], "known"
        elif tld in CCTLD:
            oc, ocs = CCTLD[tld], "domain"
        elif usd and usd[0]:
            oc, ocs = "US", "us-news"
        elif tld in GENERIC and edition != "United States" and editions_of[outlet] == {edition}:
            oc, ocs = EDITION_ISO[edition], "edition"
        else:
            oc, ocs = "unknown", "unknown"

        # type
        ot, ots = (known[1], "known") if known else (C, "default")
        if ots == "default":
            for rx, t in NAME_TYPES:
                if rx.search(outlet or ""):
                    ot, ots = t, "name"

        # leaning
        # US ratings describe US audiences and politics: used for the US edition only
        lean, ls = "unknown", "unknown"
        if edition != "United States":
            pass
        elif usd and usd[2] is not None and usd[2] in ALLSIDES:
            lean, ls = ALLSIDES[usd[2]], "allsides"
        elif usd and usd[1] is not None:
            lean, ls = bucket(usd[1]), "audience"

        m = manual.get(outlet)
        if m:
            if (m.get("outlet_country") or "").strip():
                oc, ocs = m["outlet_country"].strip(), "manual"
            if (m.get("outlet_type") or "").strip():
                ot, ots = m["outlet_type"].strip(), "manual"
            if (m.get("leaning") or "").strip():
                lean, ls = m["leaning"].strip(), (m.get("leaning_source") or "manual").strip()

        origin = "unknown" if oc == "unknown" else ("domestic" if oc == EDITION_ISO.get(edition) else "foreign")
        out.append((edition, outlet, dom, oc, ocs, ot, ots, origin, lean, ls))
    con.execute("""CREATE OR REPLACE TABLE outlet_labels (country VARCHAR, outlet VARCHAR, domain VARCHAR,
                   outlet_country VARCHAR, country_source VARCHAR, outlet_type VARCHAR, type_source VARCHAR,
                   origin VARCHAR, leaning VARCHAR, leaning_source VARCHAR)""")
    con.executemany("INSERT INTO outlet_labels VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", out)
    return len(out)


def defaultdict_set(rows):
    from collections import defaultdict
    d = defaultdict(set)
    for edition, outlet, _ in rows:
        d[outlet].add(edition)
    return d
