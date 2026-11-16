import { Card, Table, WithData } from '../components/Ui';
import { Row, int, pct, useData } from '../data';

export default function Methods() {
  const cover = useData('label_coverage');
  const kpi = useData('kpi');
  return (
    <>
      <Card title="Data">
        <ul>
          <li>Every day, the stories in the public, non-personalized Google News topic feeds of four editions (United States, France, Germany, Romania) and seven sections (World, Nation, Politics, Business, Technology, Science, Health) are collected.</li>
          <li>Each story card gives the lead article (headline, outlet, link, publication time) and up to four related articles from other outlets.</li>
          <li>The US edition is collected since January 2026, the European editions since March 2026.</li>
        </ul>
      </Card>
      <Card title="Definitions">
        <ul>
          <li><b>Lead</b>: the article Google shows on top of a story card.</li>
          <li><b>Appearance</b>: an outlet's article is in a story card, as lead or underneath.</li>
          <li><b>Lead rate</b>: leads ÷ appearances. <b>Fair lead rate</b>: the same, counting only cards with at least two outlets.</li>
          <li><b>Top-10 share</b>: share of stories led by the 10 outlets with the most leads in that edition (and section, and month, where stated).</li>
          <li><b>Domestic / foreign</b>: whether the outlet is based in the edition's country.</li>
          <li><b>Same event</b>: World and Politics headlines from two editions that are each other's closest match by meaning (multilingual sentence embeddings) within a day of each other.</li>
        </ul>
      </Card>
      <Card title="How outlets are labelled">
        <p>Every label records its source, listed in the downloadable file below.</p>
        <ul>
          <li><b>Country</b>, first match wins: (1) manual corrections; (2) a list of about 430 known outlets, matched by website; (3) the website's country code (.fr, .de, .ro, .co.uk…); (4) for .com/.org/.net websites, US news sites listed in the domain lists aggregated by Robertson et al.; (5) for .com/.org/.net websites seen only in the French, German or Romanian edition, that edition's country. Otherwise unknown.</li>
          <li><b>Type</b>: <i>public service</i> (public broadcasters with independent governance, e.g. BBC, franceinfo, ARD/ZDF, TVR), <i>state-controlled</i> (owned or directed by a government outside public-service governance, e.g. RT, CGTN, Xinhua, TRT, Al Jazeera, and US government broadcasters VOA and RFE/RL), <i>wire agency</i> (AP, Reuters, AFP, dpa, Agerpres…), <i>aggregator</i> (Yahoo, MSN, AOL…), <i>official</i> (governments and institutions), and <i>private</i> for everything else. Types come from the known-outlet list and manual corrections; an outlet not on the list counts as private.</li>
          <li><b>Political leaning</b> (US edition only): AllSides Media Bias Ratings (2018) where available, otherwise the partisan audience score of Robertson et al. (2018), from -1 (shared by Democrats) to +1 (shared by Republicans), grouped as left ≤ -0.5, lean left ≤ -0.2, center, lean right ≥ 0.2, right ≥ 0.5. Both describe US politics, so they are not applied to the European editions.</li>
        </ul>
      </Card>
      <Card title="All news sources" sub="Every outlet that appeared in a story card, per edition, with its labels and lead statistics.">
        <WithData d={kpi}>{(rows) => (
          <p>{rows.map((r: Row) => `${r.country}: ${int(r.outlets)} outlets`).join(' · ')}</p>
        )}</WithData>
        <p><a href={`${import.meta.env.BASE_URL}data/all_outlets.csv`} download>Download the full list (CSV)</a></p>
      </Card>
      <Card title="Limitations">
        <ul>
          <li>Feeds are non-personalized and collected once a day: they show Google's editorial choices for each edition, not what any reader saw.</li>
          <li>A card shows only a few of the outlets that covered a story.</li>
          <li>Outlet names are merged when they share a website; labels cover the most frequent outlets and can contain errors.</li>
          <li>Feed position comes from the order of the collected feed and may not match what readers see.</li>
          <li>Keyword, name and country counts come from simple text rules and are approximate.</li>
          <li>Some days are missing, mostly in the European editions.</li>
        </ul>
      </Card>
      <Card title="Label coverage" sub="Share of each edition's leads covered by each kind of label.">
        <WithData d={cover}>{(rows) => (
          <Table keyOf={(r) => String(r.country)} rows={rows} columns={[
            { label: 'Edition', left: true, render: (r: Row) => r.country },
            { label: 'Country known', render: (r: Row) => pct(r.leads_with_country) },
            { label: 'Country from known list or manual', render: (r: Row) => pct(r.leads_country_checked) },
            { label: 'Type from known list or manual', render: (r: Row) => pct(r.leads_type_checked) },
            { label: 'With a leaning', render: (r: Row) => pct(r.leads_with_leaning) },
          ]} />
        )}</WithData>
      </Card>
    </>
  );
}
