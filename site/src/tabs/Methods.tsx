import { Card, Table, WithData } from '../components/Ui';
import { Row, pct, useData } from '../data';

export default function Methods() {
  const cover = useData('label_coverage');
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
          <li><b>Outlet types</b>: commercial, public service, wire agency, aggregator, state-controlled (owned or directed by a government outside public-service governance), other (not labelled yet).</li>
          <li><b>Domestic / foreign</b>: whether the outlet is based in the edition's country, from its website's country code or from labels.</li>
          <li><b>Same event</b>: World and Politics headlines from two editions that are each other's closest match by meaning (multilingual sentence embeddings) within a day of each other.</li>
        </ul>
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
      <Card title="Label coverage" sub="Share of each edition's leads whose outlet has a type and a country.">
        <WithData d={cover}>{(rows) => (
          <Table keyOf={(r) => String(r.country)} rows={rows} columns={[
            { label: 'Edition', left: true, render: (r: Row) => r.country },
            { label: 'With a type', render: (r: Row) => pct(r.leads_with_type) },
            { label: 'With a country', render: (r: Row) => pct(r.leads_with_country) },
          ]} />
        )}</WithData>
      </Card>
    </>
  );
}
