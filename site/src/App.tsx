import { useEffect, useState } from 'react';
import Agenda from './tabs/Agenda';
import Compare from './tabs/Compare';
import FeedDesign from './tabs/FeedDesign';
import LeadSlot from './tabs/LeadSlot';
import Methods from './tabs/Methods';
import Outlets from './tabs/Outlets';
import Overview from './tabs/Overview';
import Timing from './tabs/Timing';

const TABS = [
  { id: 'overview', label: 'Overview', el: <Overview /> },
  { id: 'lead', label: 'Lead slot', el: <LeadSlot /> },
  { id: 'outlets', label: 'Outlets', el: <Outlets /> },
  { id: 'agenda', label: 'Agenda', el: <Agenda /> },
  { id: 'timing', label: 'Timing', el: <Timing /> },
  { id: 'feed', label: 'Feed design', el: <FeedDesign /> },
  { id: 'compare', label: 'Compare editions', el: <Compare /> },
  { id: 'methods', label: 'Data & methods', el: <Methods /> },
];

const fromHash = () => {
  const h = window.location.hash.replace('#', '');
  return TABS.some((t) => t.id === h) ? h : 'overview';
};

export default function App() {
  const [tab, setTab] = useState(fromHash);
  useEffect(() => {
    const on = () => setTab(fromHash());
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return (
    <>
      <header className="top">
        <div className="inner">
          <h1>Google News Lead Slot Observatory</h1>
          <p className="sub">Who does Google News put on top? Four editions, seven sections, every day.</p>
          <nav>
            {TABS.map((t) => (
              <a key={t.id} href={`#${t.id}`} className={t.id === tab ? 'active' : ''}>{t.label}</a>
            ))}
          </nav>
        </div>
      </header>
      <main>{TABS.find((t) => t.id === tab)!.el}</main>
    </>
  );
}
