import { useState, useEffect } from 'react';
import { fetchRevenue } from '../dataLoader';
import styles from './Revenue.module.css';

function fmtB(val) {
  if (!val) return '—';
  const b = val / 1_000_000_000;
  return b >= 1 ? `$${b.toFixed(1)}B` : `$${(val / 1_000_000).toFixed(0)}M`;
}

const CATEGORY_COLORS = {
  'Income Tax — Individuals':       '#58a6ff',
  'Income Tax — Companies':         '#3fb950',
  'Income Tax — Superannuation':    '#d29922',
  'Income Tax — Other withholding': '#bc8cff',
  'GST':                            '#f85149',
  'Excise & Customs':               '#ff7b72',
  'Fringe Benefits Tax':            '#ffa657',
  'Other Taxes':                    '#8b949e',
  'Non-Tax Revenue':                '#39d353',
};

export default function Revenue({ year }) {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchRevenue(year)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [year]);

  if (loading) return <div className={styles.loading}>Loading revenue data…</div>;
  if (!data?.by_category?.length) return (
    <div className={styles.empty}>No revenue data. Run <code>python3 seed_revenue.py</code> in the backend.</div>
  );

  // Group by year for the totals row
  const yearTotals = data.by_year ?? [];
  const grandTotal = yearTotals.reduce((s, r) => s + (r.total_aud ?? 0), 0);

  // For bar chart — aggregate by category across all selected years
  const byCat = {};
  for (const r of data.by_category) {
    byCat[r.category] = (byCat[r.category] ?? 0) + r.total_aud;
  }
  const catEntries = Object.entries(byCat).sort((a, b) => b[1] - a[1]);
  const maxCat = catEntries[0]?.[1] ?? 1;

  // Group categories by year for the table
  const years = [...new Set(data.by_category.map(r => r.year))].sort();

  return (
    <div className={styles.page}>

      {/* Header */}
      <div className={styles.header}>
        <h2 className={styles.heading}>Government Revenue</h2>
        <p className={styles.sub}>
          Federal tax and non-tax revenue from Budget Paper No. 1, Statement 5.
          {year ? ` Showing ${year}-${(parseInt(year) + 1).toString().slice(-2)}.` : ' Showing all years.'}
        </p>
      </div>

      {/* Year totals */}
      <div className={styles.yearCards}>
        {yearTotals.map(yt => (
          <div key={yt.year} className={styles.yearCard}>
            <span className={styles.yearLabel}>{yt.year}</span>
            <span className={styles.yearVal}>{fmtB(yt.total_aud)}</span>
          </div>
        ))}
      </div>

      {/* Bar chart by category */}
      <div className={styles.panel}>
        <h3 className={styles.panelTitle}>Revenue by Type</h3>
        <div className={styles.barList}>
          {catEntries.map(([cat, total]) => {
            const pct = Math.round((total / maxCat) * 100);
            const color = CATEGORY_COLORS[cat] ?? '#8b949e';
            return (
              <div key={cat} className={styles.barRow}>
                <span className={styles.barLabel}>{cat}</span>
                <div className={styles.barTrack}>
                  <div className={styles.barFill} style={{ width: `${pct}%`, background: color }} />
                </div>
                <span className={styles.barAmt}>{fmtB(total)}</span>
                <span className={styles.barPct}>{((total / grandTotal) * 100).toFixed(1)}%</span>
              </div>
            );
          })}
        </div>
        <p className={styles.source}>
          Source: Budget Paper No. 1, Statement 5 — Commonwealth Revenue.
          Figures are published estimates; Final Budget Outcome figures may differ.
        </p>
      </div>

      {/* Year-by-year detail table */}
      <div className={styles.panel}>
        <h3 className={styles.panelTitle}>Detail by Year</h3>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Revenue Source</th>
                {years.map(y => <th key={y} className={styles.num}>{y}</th>)}
              </tr>
            </thead>
            <tbody>
              {catEntries.map(([cat]) => (
                <tr key={cat}>
                  <td>
                    <span className={styles.catDot} style={{ background: CATEGORY_COLORS[cat] ?? '#8b949e' }} />
                    {cat}
                  </td>
                  {years.map(y => {
                    const match = data.by_category.find(r => r.category === cat && r.year === y);
                    return (
                      <td key={y} className={styles.num}>
                        {match ? fmtB(match.total_aud) : '—'}
                      </td>
                    );
                  })}
                </tr>
              ))}
              <tr className={styles.totalRow}>
                <td><strong>Total</strong></td>
                {years.map(y => {
                  const yt = yearTotals.find(r => r.year === y);
                  return (
                    <td key={y} className={styles.num}>
                      <strong>{yt ? fmtB(yt.total_aud) : '—'}</strong>
                    </td>
                  );
                })}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
