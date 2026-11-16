import { useState } from 'react';
import { Lines, StackedArea } from '../components/Plots';
import { Card, EditionPicker, WithData } from '../components/Ui';
import { COUNTRIES, dayLabel, int, monthLabel, pct, pivot, useData } from '../data';

export default function FeedDesign() {
  const size = useData('cluster_size_monthly');
  const link = useData('link_phrase_weekly');
  const cov = useData('coverage_daily');
  const [ed, setEd] = useState('United States');
  return (
    <>
      <Card title="How big are story cards?" sub="Average number of articles per story card, and share of cards with a single article.">
        <WithData d={size}>{(rows) => (
          <div className="grid2">
            <div><h3>Articles per card</h3>
              <Lines data={pivot(rows, 'month', 'country', 'avg_cluster_size')} keys={[...COUNTRIES]}
                yFormat={(v) => v.toFixed(1)} xFormat={monthLabel} height={240} dots /></div>
            <div><h3>Single-article cards</h3>
              <Lines data={pivot(rows, 'month', 'country', 'single_share')} keys={[...COUNTRIES]}
                yFormat={(v) => pct(v)} xFormat={monthLabel} height={240} yDomain={[0, 1]} dots /></div>
          </div>
        )}</WithData>
      </Card>
      <Card title="Changes in Google's design"
        sub="Wording of the “full coverage” link at the end of story cards, week by week. A switch from one wording to another marks a change in how Google News presents stories.">
        <EditionPicker value={ed} onChange={setEd} />
        <WithData d={link}>{(rows) => {
          const r = rows.filter((x) => x.country === ed);
          const keys = [...new Set(r.map((x) => x.link_phrase as string))];
          return <StackedArea data={pivot(r, 'week', 'link_phrase', 'stories')} keys={keys} shares xFormat={dayLabel} />;
        }}</WithData>
      </Card>
      <Card title="Stories collected per day" sub="Gaps are days when the collector got nothing back.">
        <WithData d={cov}>{(rows) => (
          <Lines data={pivot(rows.filter((r) => r.stories > 0), 'date', 'country', 'stories')} keys={[...COUNTRIES]}
            xFormat={dayLabel} yFormat={int} />
        )}</WithData>
      </Card>
    </>
  );
}
