import { SECTORS } from '../data';
import styles from './OverviewTable.module.css';

function fmtB(val) {
  if (val == null) return null;
  const b = val / 1_000_000_000;
  return b >= 1 ? `$${b.toFixed(1)}B` : `$${(val / 1_000_000).toFixed(0)}M`;
}

export default function OverviewTable({ activeSector, sectorTotals }) {
  const rows = activeSector
    ? Object.entries(SECTORS).filter(([k]) => k === activeSector)
    : Object.entries(SECTORS);

  return (
    <div className={styles.panel}>
      <h2 className={styles.title}>All Sectors Overview</h2>
      <div className={styles.wrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Sector</th>
              <th>Top Agency</th>
              <th className={styles.num}>Records</th>
              <th className={styles.num}>Tracked Spend</th>
              <th>Plain-English Summary</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([key, s]) => {
              const live = sectorTotals[key];
              const amt  = live?.total ?? null;
              const cnt  = live?.count ?? null;
              return (
                <tr key={key}>
                  <td>
                    <span className={styles.dot} style={{ background: s.color }} />
                    <strong>{s.label}</strong>
                  </td>
                  <td><span className={styles.agency}>{s.overview_agency}</span></td>
                  <td className={styles.num}>
                    {cnt != null ? cnt.toLocaleString() : <span className={styles.placeholder}>—</span>}
                  </td>
                  <td className={styles.num}>
                    {amt != null
                      ? <strong>{fmtB(amt)}</strong>
                      : <span className={styles.placeholder}>— awaiting data</span>}
                  </td>
                  <td className={styles.summary}>{s.overview_summary}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
