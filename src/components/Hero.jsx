import styles from './Hero.module.css';

function fmtB(val) {
  if (val == null) return '—';
  const b = val / 1_000_000_000;
  return b >= 1 ? `$${b.toFixed(1)}B` : `$${(val / 1_000_000).toFixed(0)}M`;
}

export default function Hero({ sectorTotals, loading }) {
  const totalSpend   = Object.values(sectorTotals).reduce((s, v) => s + (v.total ?? 0), 0) || null;
  const totalPrograms = Object.values(sectorTotals).reduce((s, v) => s + (v.count ?? 0), 0) || null;

  return (
    <section className={styles.hero}>
      <div className={styles.inner}>
        <div className={styles.card}>
          <span className={styles.label}>Spending Tracked</span>
          <span className={styles.value}>{loading ? '…' : fmtB(totalSpend)}</span>
          <span className={styles.sub}>Across all datasets</span>
        </div>
        <div className={styles.card}>
          <span className={styles.label}>Total Revenue</span>
          <span className={styles.value}>—</span>
          <span className={styles.sub}>Not yet ingested</span>
        </div>
        <div className={styles.card}>
          <span className={styles.label}>Budget Deficit / Surplus</span>
          <span className={styles.value}>—</span>
          <span className={styles.sub}>Not yet ingested</span>
        </div>
        <div className={styles.card}>
          <span className={styles.label}>Records Tracked</span>
          <span className={styles.value}>{loading ? '…' : (totalPrograms?.toLocaleString() ?? '—')}</span>
          <span className={styles.sub}>Spending line items</span>
        </div>
      </div>
    </section>
  );
}
