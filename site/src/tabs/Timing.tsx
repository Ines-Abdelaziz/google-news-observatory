import { useState } from 'react';
import { Heatmap, StackedBars } from '../components/Plots';
import { Card, CategoryPicker, EditionPicker, WithData } from '../components/Ui';
import { CATEGORIES, COUNTRIES, Row, WEEKDAYS, int, pct, pivot, toShares, useData } from '../data';

const AGES = ['same day', '1 day', '2-3 days', '4-7 days', 'older'];
const HOURS = Array.from({ length: 24 }, (_, h) => String(h));
const DAYS = [1, 2, 3, 4, 5, 6, 0].map(String); // Monday first

export default function Timing() {
  const hours = useData('publication_hours');
  const fresh = useData('freshness');
  const wd = useData('weekday_mix');
  const [ed, setEd] = useState('United States');
  const [cat, setCat] = useState('All');
  return (
    <>
      <Card title="When are lead articles published?" sub="Lead articles by weekday and hour of publication, in the edition's local time.">
        <EditionPicker value={ed} onChange={setEd} />
        <WithData d={hours}>{(rows) => {
          const r = rows.filter((x) => x.country === ed);
          const total = r.reduce((s, x) => s + x.stories, 0) || 1;
          return <Heatmap rows={DAYS} cols={HOURS} rowLabel={(d) => WEEKDAYS[+d]} format={(v) => pct(v, 1)}
            value={(d, h) => (r.find((x) => String(x.weekday) === d && String(x.hour) === h)?.stories ?? 0) / total} />;
        }}</WithData>
      </Card>
      <Card title="How fresh are lead articles?" sub="Age of the lead article on the day of the feed snapshot.">
        <CategoryPicker value={cat} onChange={setCat} withAll />
        <WithData d={fresh}>{(rows) => {
          const r = cat === 'All' ? rows : rows.filter((x) => x.category === cat);
          const p = pivot(r, 'country', 'age_bucket', 'stories');
          const ordered = COUNTRIES.map((c) => p.find((x) => x.x === c)).filter(Boolean) as Row[];
          return <StackedBars data={toShares(ordered, AGES)} keys={AGES} />;
        }}</WithData>
      </Card>
      <Card title="Section mix by weekday" sub="Share of each section in the edition's stories, by day of the week.">
        <EditionPicker value={ed} onChange={setEd} />
        <WithData d={wd}>{(rows) => {
          const r = rows.filter((x) => x.country === ed);
          const tot = Object.fromEntries(DAYS.map((d) => [d, r.filter((x) => String(x.weekday) === d).reduce((s, x) => s + x.stories, 0) || 1]));
          return <Heatmap rows={[...CATEGORIES]} cols={DAYS} colLabel={(d) => WEEKDAYS[+d]} format={(v) => pct(v)}
            value={(c, d) => (r.find((x) => x.category === c && String(x.weekday) === d)?.stories ?? 0) / tot[d]} />;
        }}</WithData>
        <p className="note">Stories: {int((wd.data ?? []).filter((x) => x.country === ed).reduce((s, x) => s + x.stories, 0))}</p>
      </Card>
    </>
  );
}
