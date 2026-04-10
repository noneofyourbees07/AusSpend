import { useState, useEffect } from 'react';
import Header        from './components/Header';
import Hero          from './components/Hero';
import FilterBar     from './components/FilterBar';
import SectorPanel   from './components/SectorPanel';
import BarChart      from './components/BarChart';
import NewsPanel     from './components/NewsPanel';
import OverviewTable from './components/OverviewTable';
import Dashboard     from './pages/Dashboard';
import Revenue       from './pages/Revenue';
import Sources       from './pages/Sources';
import Debt          from './pages/Debt';
import Scope         from './pages/Scope';
import NoData        from './components/NoData';
import { SECTORS }   from './data';
import styles        from './App.module.css';

export default function App() {
  const [page, setPage]                 = useState('dashboard');
  const [year, setYear]                 = useState('');
  const [activeSector, setSector]       = useState('welfare');
  const [search, setSearch]             = useState('');
  const [sectorFilter, setSectorFilter] = useState('');
  const [stateFilter, setStateFilter]   = useState('');

  // Shared API data (fetched once, passed to all pages)
  const [sectorTotals, setSectorTotals] = useState({});
  const [yearSummary,  setYearSummary]  = useState({});
  const [revenueData,  setRevenueData]  = useState(null);
  const [apiLoading,   setApiLoading]   = useState(true);

  useEffect(() => {
    setApiLoading(true);
    const yearParam = year ? `?year=${year}` : '';
    Promise.all([
      fetch(`/api/sectors${yearParam}`).then(r => r.json()),
      fetch('/api/spending/summary').then(r => r.json()),
      fetch('/api/revenue').then(r => r.json()).catch(() => null),
    ])
      .then(([sectors, summary, revenue]) => {
        const totals = {};
        for (const row of sectors) {
          totals[row.sector] = { total: row.total_aud, count: row.program_count };
        }
        setSectorTotals(totals);
        setYearSummary(summary);
        setRevenueData(revenue);
      })
      .catch(err => console.error('API error:', err))
      .finally(() => setApiLoading(false));
  }, [year]);  // re-runs whenever year changes

  function handleSectorFilter(val) {
    setSectorFilter(val);
    if (val && SECTORS[val]) setSector(val);
  }

  function handleClear() {
    setSearch('');
    setSectorFilter('');
    setStateFilter('');
  }

  const sectorMeta  = SECTORS[activeSector];
  const sectorTotal = sectorTotals[activeSector]?.total ?? null;

  const chartData = (() => {
    const yearMap = yearSummary[activeSector] ?? {};
    return ['2020-21', '2021-22', '2022-23', '2023-24'].map(y =>
      yearMap[y] ?? yearMap[y.replace('-', '–')] ?? null
    );
  })();

  return (
    <>
      <Header
        page={page}
        onNavigate={setPage}
        year={year}
        onYearChange={setYear}
      />

      <main className={styles.main}>
        {page === 'dashboard' && (
          <Dashboard
            sectorTotals={sectorTotals}
            revenueData={revenueData}
            loading={apiLoading}
            onNavigate={setPage}
          />
        )}

        {page === 'spending' && (
          <>
            <Hero sectorTotals={sectorTotals} loading={apiLoading} />
            {!apiLoading && Object.keys(sectorTotals).length === 0 && (
              <NoData year={year} reason="year" />
            )}
            <FilterBar
              search={search}
              sector={sectorFilter}
              state={stateFilter}
              onSearch={setSearch}
              onSector={handleSectorFilter}
              onState={setStateFilter}
              onClear={handleClear}
            />
            <div className={styles.grid}>
              <SectorPanel
                activeSector={activeSector}
                onSectorChange={setSector}
                search={search}
                sectorTotal={sectorTotal}
                year={year}
                state={stateFilter}
              />
              <div className={styles.side}>
                <BarChart sectorMeta={sectorMeta} chartData={chartData} />
                <NewsPanel sector={sectorMeta} />
              </div>
            </div>
            <OverviewTable activeSector={sectorFilter} sectorTotals={sectorTotals} />
          </>
        )}

        {page === 'revenue' && <Revenue year={year} />}

        {page === 'debt'    && <Debt />}
        {page === 'scope'   && <Scope />}
        {page === 'sources' && <Sources />}
      </main>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <span>
            AusSpend — open data from{' '}
            <a href="https://data.gov.au" target="_blank" rel="noreferrer">data.gov.au</a>,{' '}
            <a href="https://budget.gov.au" target="_blank" rel="noreferrer">budget.gov.au</a>,{' '}
            <a href="https://www.finance.gov.au" target="_blank" rel="noreferrer">Dept. of Finance</a>.
          </span>
          <span className={styles.footerRight}>
            Not affiliated with the Australian Government.
          </span>
        </div>
      </footer>
    </>
  );
}

function fmtB(val) {
  if (!val) return '—';
  const b = val / 1_000_000_000;
  return b >= 1 ? `$${b.toFixed(1)}B` : `$${(val / 1_000_000).toFixed(0)}M`;
}
