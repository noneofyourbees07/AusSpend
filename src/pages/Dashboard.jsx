import { useState } from 'react';
import DonutChart from '../components/DonutChart';
import { SECTORS } from '../data';
import styles from './Dashboard.module.css';

function fmtB(val) {
  if (!val) return '—';
  const b = val / 1_000_000_000;
  return b >= 1 ? `$${b.toFixed(1)}B` : `$${(val / 1_000_000).toFixed(0)}M`;
}

// Stub news cards — replaced by API later
const STUB_NEWS = [
  { sector: 'welfare',  headline: 'NDIS cost blowout prompts independent review of eligibility', source: 'ABC News', date: 'Mar 2024' },
  { sector: 'health',   headline: 'Medicare bulk billing incentives expanded in budget update', source: 'The Guardian', date: 'Apr 2024' },
  { sector: 'defence',  headline: 'AUKUS submarine costs projected to reach $368bn over 40 years', source: 'AFR', date: 'Mar 2024' },
  { sector: 'education','headline': 'HECS debt indexation controversy prompts reform calls', source: 'ABC News', date: 'Apr 2024' },
  { sector: 'infrastructure', headline: 'Infrastructure Investment Program projects face cost overruns', source: 'SMH', date: 'Feb 2024' },
  { sector: 'environment','headline': 'Rewiring the Nation — transmission approvals fast-tracked', source: 'The Guardian', date: 'Apr 2024' },
];

export default function Dashboard({ sectorTotals, revenueData, loading, onNavigate }) {
  const [hovered, setHovered] = useState(null);

  const totalSpend   = Object.values(sectorTotals).reduce((s, v) => s + (v.total ?? 0), 0) || null;
  const totalRecords = Object.values(sectorTotals).reduce((s, v) => s + (v.count ?? 0), 0) || null;

  // Show latest single year revenue, not sum of all years
  const latestRevYear = revenueData?.by_year?.slice(-1)[0];
  const totalRevenue  = latestRevYear?.total_aud ?? null;
  const revYearLabel  = latestRevYear?.year ?? '';

  // National debt — context figure from AOFM (~$1.07T)
  const nationalDebt = 1_070_000_000_000;

  // Deficit/surplus — revenue minus spending (negative = deficit)
  const balance = (totalRevenue && totalSpend) ? totalRevenue - totalSpend : null;
  const isDeficit = balance != null && balance < 0;

  const topSector = Object.entries(sectorTotals)
    .sort((a, b) => (b[1].total ?? 0) - (a[1].total ?? 0))[0];

  return (
    <div className={styles.page}>

      {/* ── Big 4 stat row: Revenue, Spending, Balance, Debt ── */}
      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Money In (Revenue)</span>
          <span className={styles.statVal} style={{ color: '#3fb950' }}>{loading ? '…' : fmtB(totalRevenue)}</span>
          <span className={styles.statSub}>{revYearLabel || 'Latest'} · federal taxes &amp; non-tax</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Money Out (Spending)</span>
          <span className={styles.statVal} style={{ color: '#f85149' }}>{loading ? '…' : fmtB(totalSpend)}</span>
          <span className={styles.statSub} title="Includes the 10 main sectors. Real total is ~$700B once you add grants to states, debt interest, contingency, and foreign aid.">
            partial · hover for note
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>{isDeficit ? 'Deficit' : 'Surplus'} (this year)</span>
          <span className={styles.statVal} style={{ color: isDeficit ? '#f85149' : '#3fb950' }}>
            {loading || balance == null ? '…' : (isDeficit ? '−' : '+') + fmtB(Math.abs(balance))}
          </span>
          <span className={styles.statSub}>Revenue − Spending (partial figures)</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>National Debt</span>
          <span className={styles.statVal} style={{ color: '#d29922' }}>$1.07T</span>
          <span className={styles.statSub}>Commonwealth Govt Securities (AOFM)</span>
        </div>
      </div>

      {/* ── Why doesn't it add up? Explainer banner ── */}
      <div className={styles.explainer}>
        <span className={styles.explainerIcon}>i</span>
        <div>
          <strong>Why doesn&rsquo;t the money in/out match the debt?</strong>
          <p className={styles.explainerBody}>
            Even when revenue covers most spending, Australia has run deficits for years.
            The shortfall is borrowed by issuing Treasury Bonds — that&rsquo;s the $1.07 trillion debt.
            Annual interest on the debt (~$20B) is itself a spending line.
            This dashboard shows <strong>federal</strong> figures only — state taxes (rego, stamp duty,
            land tax) and council rates are tracked separately by each state and council.
          </p>
        </div>
      </div>

      {/* ── Main grid ── */}
      <div className={styles.grid}>

        {/* Donut chart panel */}
        <div className={styles.panel}>
          <div className={styles.panelHead}>
            <h2 className={styles.panelTitle}>Spending by Sector</h2>
            <span className={styles.panelNote}>Hover to explore · click sector to drill in</span>
          </div>
          <DonutChart
            sectorTotals={sectorTotals}
            hovered={hovered}
            onHover={setHovered}
          />
          <p className={styles.dataNote}>
            Data from <a href="https://data.gov.au" target="_blank" rel="noreferrer">data.gov.au</a>.
            Partial dataset — not all programs are captured yet.{' '}
            <button className={styles.linkBtn} onClick={() => onNavigate('sources')}>
              View sources →
            </button>
          </p>
        </div>

        {/* Revenue breakdown panel */}
        <div className={styles.panel}>
          <div className={styles.panelHead}>
            <h2 className={styles.panelTitle}>Revenue by Type</h2>
            <span className={styles.panelNote}>Government income — tax &amp; non-tax</span>
          </div>
          {revenueData?.by_category?.length > 0 ? (
            <div className={styles.revList}>
              {revenueData.by_category.slice(0, 8).map((r, i) => {
                const max = revenueData.by_category[0]?.total_aud ?? 1;
                const pct = Math.round((r.total_aud / max) * 100);
                return (
                  <div key={i} className={styles.revRow}>
                    <span className={styles.revLabel}>{r.category}</span>
                    <div className={styles.revBarWrap}>
                      <div className={styles.revBar} style={{ width: `${pct}%` }} />
                    </div>
                    <span className={styles.revAmt}>{fmtB(r.total_aud)}</span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className={styles.revEmpty}>
              <p>Revenue data not yet loaded.</p>
              <p className={styles.revEmptyHint}>
                Run <code>fetch_revenue.py</code> then <code>parse_revenue.py</code> in the backend to populate this.
              </p>
              <div className={styles.revCategories}>
                <p className={styles.revCatTitle}>What will appear here:</p>
                {['Income Tax — Individuals', 'Income Tax — Companies', 'GST',
                  'Excise & Customs', 'Income Tax — Superannuation', 'Non-Tax Revenue'].map(c => (
                  <div key={c} className={styles.revCatRow}>
                    <span className={styles.revCatDot} />
                    <span>{c}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Sources & Disclaimer ── */}
      <div className={styles.sourcesPanel}>
        <div className={styles.sourcesHead}>
          <h2 className={styles.panelTitle}>Where this data comes from</h2>
          <span className={styles.panelNote}>All figures are from official Australian Government publications</span>
        </div>

        <div className={styles.sourceGrid}>
          <div className={styles.sourceCard}>
            <div className={styles.sourceIcon} style={{ background: '#1f6feb', color: '#58a6ff' }}>$</div>
            <div className={styles.sourceContent}>
              <h4 className={styles.sourceTitle}>Federal Spending &amp; Revenue</h4>
              <p className={styles.sourceDesc}>
                Headline sector totals from <strong>Budget Paper No. 1, Statement 5 &amp; 6</strong>,
                published annually by the Treasury each May.
              </p>
              <a href="https://budget.gov.au" target="_blank" rel="noreferrer" className={styles.sourceLink}>
                budget.gov.au →
              </a>
            </div>
          </div>

          <div className={styles.sourceCard}>
            <div className={styles.sourceIcon} style={{ background: 'rgba(248,81,73,0.2)', color: '#f85149' }}>%</div>
            <div className={styles.sourceContent}>
              <h4 className={styles.sourceTitle}>Individual Contracts (2014–2019)</h4>
              <p className={styles.sourceDesc}>
                240,000 contract records from <strong>AusTender</strong>, the Commonwealth&rsquo;s
                official procurement publication system. Sourced via data.gov.au CKAN API.
              </p>
              <a href="https://www.tenders.gov.au" target="_blank" rel="noreferrer" className={styles.sourceLink}>
                tenders.gov.au →
              </a>
            </div>
          </div>

          <div className={styles.sourceCard}>
            <div className={styles.sourceIcon} style={{ background: 'rgba(210,153,34,0.2)', color: '#d29922' }}>D</div>
            <div className={styles.sourceContent}>
              <h4 className={styles.sourceTitle}>National Debt</h4>
              <p className={styles.sourceDesc}>
                Commonwealth Government Securities outstanding from the
                <strong> Australian Office of Financial Management (AOFM)</strong>,
                which manages all Commonwealth debt issuance.
              </p>
              <a href="https://aofm.gov.au/statistics" target="_blank" rel="noreferrer" className={styles.sourceLink}>
                aofm.gov.au/statistics →
              </a>
            </div>
          </div>

          <div className={styles.sourceCard}>
            <div className={styles.sourceIcon} style={{ background: 'rgba(63,185,80,0.2)', color: '#3fb950' }}>H</div>
            <div className={styles.sourceContent}>
              <h4 className={styles.sourceTitle}>HECS / HELP Student Loans</h4>
              <p className={styles.sourceDesc}>
                Loan book figures from the <strong>Department of Education</strong> annual
                HELP statistics. Repayment data via ATO Taxation Statistics.
              </p>
              <a href="https://www.education.gov.au/higher-education-statistics" target="_blank" rel="noreferrer" className={styles.sourceLink}>
                education.gov.au →
              </a>
            </div>
          </div>
        </div>

        <div className={styles.disclaimer}>
          <strong>Disclaimer:</strong> AusSpend is an independent open-data project,
          not affiliated with or endorsed by the Australian Government. All figures are
          published by official sources but may differ from final outcomes — Budget
          estimates change as the year progresses, and Final Budget Outcome documents
          (published each September) are the authoritative settled figures. Always
          verify large numbers against the original source before citing.
          <br /><br />
          This dashboard shows <strong>federal</strong> figures only. State taxes
          (rego, stamp duty, land tax, payroll tax) and local council rates are
          collected and spent separately — see <button className={styles.inlineLink} onClick={() => onNavigate('scope')}>Data Scope</button> for the full breakdown.
          <br /><br />
          Built with publicly available data for civic transparency. Source code is open.
          For corrections or questions, raise an issue on GitHub.
        </div>
      </div>

      {/* ── News cards ── */}
      <div className={styles.newsSection}>
        <div className={styles.newsSectionHead}>
          <h2 className={styles.panelTitle}>Latest News &amp; Context</h2>
          <span className={styles.panelNote}>News enrichment layer — coming soon from live feeds</span>
        </div>
        <div className={styles.newsGrid}>
          {STUB_NEWS.map((n, i) => (
            <div key={i} className={styles.newsCard}>
              <span
                className={styles.newsCardTag}
                style={{ background: SECTORS[n.sector]?.color + '22',
                         color: SECTORS[n.sector]?.color }}
              >
                {SECTORS[n.sector]?.label?.split(' ')[0]}
              </span>
              <p className={styles.newsCardHeadline}>{n.headline}</p>
              <span className={styles.newsCardMeta}>{n.source} · {n.date}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
