import { SECTORS } from '../data';
import styles from './DonutChart.module.css';

const SIZE   = 220;
const RADIUS = 80;
const CX     = SIZE / 2;
const CY     = SIZE / 2;
const CIRC   = 2 * Math.PI * RADIUS;
const GAP    = 2; // px gap between segments

function fmtB(val) {
  if (!val) return '—';
  const b = val / 1_000_000_000;
  return b >= 1 ? `$${b.toFixed(1)}B` : `$${(val / 1_000_000).toFixed(0)}M`;
}

export default function DonutChart({ sectorTotals, onHover, hovered }) {
  const entries = Object.entries(SECTORS)
    .map(([key, s]) => ({ key, label: s.label, color: s.color, total: sectorTotals[key]?.total ?? 0 }))
    .filter(e => e.total > 0)
    .sort((a, b) => b.total - a.total);

  const grandTotal = entries.reduce((s, e) => s + e.total, 0);
  if (grandTotal === 0) {
    return <div className={styles.empty}>Loading chart…</div>;
  }

  // Build segments
  let offset = 0;
  const segments = entries.map(e => {
    const pct    = e.total / grandTotal;
    const length = Math.max(pct * CIRC - GAP, 0);
    const seg    = { ...e, pct, length, offset };
    offset += pct * CIRC;
    return seg;
  });

  const active = hovered ? entries.find(e => e.key === hovered) : null;

  return (
    <div className={styles.wrap}>
      <div className={styles.chartArea}>
        <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className={styles.svg}>
          {segments.map(seg => (
            <circle
              key={seg.key}
              cx={CX} cy={CY} r={RADIUS}
              fill="none"
              stroke={seg.color}
              strokeWidth={hovered === seg.key ? 28 : 22}
              strokeDasharray={`${seg.length} ${CIRC}`}
              strokeDashoffset={-seg.offset}
              strokeLinecap="butt"
              style={{ transition: 'stroke-width 0.2s, opacity 0.2s', cursor: 'pointer',
                       opacity: hovered && hovered !== seg.key ? 0.35 : 1 }}
              onMouseEnter={() => onHover(seg.key)}
              onMouseLeave={() => onHover(null)}
            />
          ))}
          {/* Centre label */}
          <text x={CX} y={CY - 10} textAnchor="middle" className={styles.centreVal}>
            {active ? fmtB(active.total) : fmtB(grandTotal)}
          </text>
          <text x={CX} y={CY + 12} textAnchor="middle" className={styles.centreLabel}>
            {active ? active.label.split(' ')[0] : 'Total tracked'}
          </text>
        </svg>
      </div>

      <ul className={styles.legend}>
        {segments.map(seg => (
          <li
            key={seg.key}
            className={`${styles.legendItem} ${hovered === seg.key ? styles.legendActive : ''}`}
            onMouseEnter={() => onHover(seg.key)}
            onMouseLeave={() => onHover(null)}
          >
            <span className={styles.legendDot} style={{ background: seg.color }} />
            <span className={styles.legendLabel}>{seg.label}</span>
            <span className={styles.legendAmt}>{fmtB(seg.total)}</span>
            <span className={styles.legendPct}>{(seg.pct * 100).toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
