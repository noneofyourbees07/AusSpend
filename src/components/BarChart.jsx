import styles from './BarChart.module.css';

const YEAR_LABELS = ['2020–21', '2021–22', '2022–23', '2023–24'];

function fmtB(val) {
  if (val == null) return '—';
  const b = val / 1_000_000_000;
  return b >= 0.1 ? `$${b.toFixed(1)}B` : `$${(val / 1_000_000).toFixed(0)}M`;
}

export default function BarChart({ sectorMeta, chartData }) {
  const hasData = chartData.some(v => v != null);
  const maxVal  = Math.max(...chartData.filter(v => v != null), 1);

  return (
    <div className={styles.panel}>
      <h3 className={styles.title}>
        Year-on-Year Spending <span className={styles.sub}>— {sectorMeta.label}</span>
      </h3>
      <div className={styles.wrap}>
        <div className={styles.chart}>
          {chartData.map((v, i) => {
            const height = v != null ? Math.max(Math.round((v / maxVal) * 100), 4) : 18;
            return (
              <div key={i} className={styles.col}>
                <span className={styles.topLabel}>{fmtB(v)}</span>
                <div
                  className={`${styles.bar} ${i === chartData.length - 1 ? styles.active : ''}`}
                  style={{
                    height: `${height}px`,
                    background: v != null ? sectorMeta.color : undefined,
                    opacity: v != null ? 0.7 : 0.2,
                  }}
                  title={`${YEAR_LABELS[i]}: ${fmtB(v)}`}
                />
              </div>
            );
          })}
        </div>
        <div className={styles.axis}>
          {YEAR_LABELS.map(y => (
            <span key={y} className={styles.axisLabel}>{y}</span>
          ))}
        </div>
      </div>
      {!hasData && <p className={styles.note}>Year breakdown not available for this sector yet.</p>}
      {hasData  && <p className={styles.note}>$AUD. Source: data.gov.au — partial dataset.</p>}
    </div>
  );
}
