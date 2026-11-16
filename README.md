# Google News Lead Slot Observatory

**Who does Google News put on top?**

When several outlets cover the same story, Google News groups their articles into a single
story card. It shows one article as the **lead**, the large one on top, and a few others
underneath. That choice decides which outlet gets the reader's attention, and the traffic.

This observatory tracks that choice every day in four country editions of Google News:
**United States, France, Germany and Romania**. It covers seven sections: World, Nation,
Politics, Business, Technology, Science and Health.

🔗 **Live site:** _coming soon_

---

## What it shows

- **Lead slot.** How concentrated it is in each edition and section, which outlets lead most
  often, their lead rate, who gets the first positions of the feed, and whether lead headlines
  differ from the others.
- **Outlets.** How many outlets make it into the feeds, new outlets each month, outlet types
  (public service, commercial, wire agencies, aggregators, state-controlled media), domestic vs
  foreign outlets, which outlets appear together, and a profile for each major outlet.
- **Agenda.** The mix of sections over time, the words, names and countries that stand out,
  how long stories stay, and stories filed in several sections.
- **Timing.** When lead articles are published and how fresh they are.
- **Feed design.** The size of story cards over time, and changes in how Google presents them.
- **Compare editions.** How alike the editions are in who leads World news, outlets leading in
  several editions, and the same events covered across editions.

## How the data is collected

Every day, we collect the stories in the public, non-personalized Google News topic feeds of
each edition. Each story card gives us:

- the **lead article**: its headline, outlet, link and publication time
- the **related articles** Google shows underneath it, usually up to four, from other outlets

From these we count, for every outlet:

- **Leads:** how many stories it led
- **Appearances:** how many story cards it appeared in, as lead or underneath
- **Lead rate:** leads ÷ appearances
- **Fair lead rate:** the same, counting only stories with at least two outlets. In a
  single-article story the only outlet leads by default, so this is where Google really
  makes a choice.

## Limitations

- **Editorial supply, not exposure.** The feeds are non-personalized and collected once a
  day. They show Google's editorial choices for each edition, not what any individual reader
  saw.
- **Clusters are partial.** A story card shows only a few of the outlets that covered the
  story, so "appearances" means appearing among those shown.
- **Outlet names come from Google.** Names that share a website are merged; aggregators that
  republish other outlets' articles are counted as outlets.
- **Labels and text analyses are approximate.** Outlet types and countries cover the most
  frequent outlets; keywords, names and countries come from simple text rules; event matching
  uses a multilingual language model and can link or miss stories.
- **Collection gaps.** Some days are missing, mostly in the European editions. The site
  shows them.
- **Coverage starts at different dates.** The US edition starts in January 2026, the
  European editions in March 2026.

## Data availability

Raw data is not published in this repository. The aggregated results shown on the site are in
[`site/public/data/`](site/public/data/) as JSON files.

Researchers who want access to the underlying story-level data can contact us (see below).

## Repository structure

| Folder | Contents |
|---|---|
| `pipeline/` | Python code that parses the daily feeds into tables (`build_tables.py`), the SQL aggregates computed with DuckDB (`sql/`, `export_json.py`), outlet labels (`labels.py`, `labels/`), headline text analyses (`text_analyses.py`) and cross-edition event matching (`events.py`) |
| `site/` | The website: a static React + Vite app that reads the JSON files |
| `docs/` | Notes for maintainers |

To rebuild the site locally:

```bash
cd site
npm install
npm run dev
```

## Team

Ines Abdelaziz, Inria and Institut Polytechnique de Paris.

## How to cite

_Citation to be added._

## License

_To be decided._

## Contact

Ines Abdelaziz, [@Ines-Abdelaziz](https://github.com/Ines-Abdelaziz). Questions, corrections
and requests from outlets or researchers are welcome through
[GitHub issues](https://github.com/Ines-Abdelaziz/google-news-observatory/issues).
