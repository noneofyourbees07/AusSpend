import { useState, useEffect } from 'react';
import styles from './Debt.module.css';

function fmtB(val) {
  if (val == null) return '—';
  const b = val / 1_000_000_000;
  if (b >= 1000) return `$${(b / 1000).toFixed(2)}T`;
  if (b >= 1)    return `$${b.toFixed(1)}B`;
  return `$${(val / 1_000_000).toFixed(0)}M`;
}

// Known context figures — from Budget Papers / AOFM published data
// These are updated manually when new Budget Papers are released.
const KNOWN_DEBT = {
  label:       'Commonwealth Government Securities on issue',
  asAt:        'March 2025 (approximate)',
  total:       1_070_000_000_000,  // ~$1.07 trillion face value
  source:      'AOFM — aofm.gov.au/statistics',
  sourceUrl:   'https://aofm.gov.au/statistics/domestic-government-securities',
  instruments: [
    { name: 'Treasury Bonds',        amount: 970_000_000_000,  note: 'Long-term fixed interest, 2–30 year maturity' },
    { name: 'Treasury Indexed Bonds',amount: 60_000_000_000,   note: 'CPI-linked, inflation-protected bonds' },
    { name: 'Treasury Notes',        amount: 40_000_000_000,   note: 'Short-term bills, <1 year maturity' },
  ],
  interest_pa:  20_000_000_000,   // ~$20B interest/year from 2024-25 budget
  interest_source: '2024-25 Budget Papers — interest on debt',
};

// HECS/HELP known context figures — from Dept of Education annual reports
const KNOWN_HECS = {
  total_outstanding: 74_000_000_000,  // ~$74B as at 2023
  borrowers:         3_200_000,        // ~3.2M active debtors
  avg_debt:          23_000,           // ~$23,000 average
  annual_repayments: 5_000_000_000,    // ~$5B repaid annually via ATO
  annual_new_loans:  11_000_000_000,   // ~$11B new loans issued each year
  write_offs:        400_000_000,      // ~$400M written off (deaths, permanent disability)
  indexation_2023:   7.1,              // 7.1% CPI indexation applied June 2023
  indexation_2024:   4.7,              // 4.7% CPI indexation applied June 2024
  source:            'Dept of Education — HELP annual report 2023',
  sourceUrl:         'https://www.education.gov.au/higher-education-statistics/student-data/help-statistics',
};

export default function Debt() {
  const [debtData, setDebtData] = useState(null);
  const [hecsData, setHecsData] = useState(null);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/debt').then(r => r.json()).catch(() => null),
      fetch('/api/hecs').then(r => r.json()).catch(() => null),
    ]).then(([debt, hecs]) => {
      setDebtData(debt);
      setHecsData(hecs);
    }).finally(() => setLoading(false));
  }, []);

  const hasDebtData = debtData?.record_count > 0;
  const hasHecsData = hecsData?.record_count > 0;

  // Use live data if available, otherwise fall back to known context figures
  const debtTotal = hasDebtData
    ? debtData.by_instrument.reduce((s, r) => s + r.face_value_aud, 0)
    : KNOWN_DEBT.total;

  const hecsOutstanding = hasHecsData
    ? hecsData.outstanding_trend.slice(-1)[0]?.total_aud
    : KNOWN_HECS.total_outstanding;

  return (
    <div className={styles.page}>

      {/* ── National debt ── */}
      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <h2 className={styles.heading}>National Debt</h2>
          <span className={styles.sub}>Commonwealth Government Securities (CGS) on issue</span>
        </div>

        <div className={styles.statRow}>
          <div className={styles.bigStat}>
            <span className={styles.bigLabel}>Total CGS Outstanding</span>
            <span className={styles.bigVal} style={{ color: '#f85149' }}>{fmtB(debtTotal)}</span>
            <span className={styles.bigNote}>
              {hasDebtData ? `Live from database · ${debtData.record_count} records` : `Context figure · ${KNOWN_DEBT.asAt}`}
            </span>
          </div>
          <div className={styles.bigStat}>
            <span className={styles.bigLabel}>Annual Interest Cost</span>
            <span className={styles.bigVal}>{fmtB(KNOWN_DEBT.interest_pa)}</span>
            <span className={styles.bigNote}>{KNOWN_DEBT.interest_source}</span>
          </div>
          <div className={styles.bigStat}>
            <span className={styles.bigLabel}>Interest as % of Spending</span>
            <span className={styles.bigVal}>~4.8%</span>
            <span className={styles.bigNote}>Based on ~$420B total federal spending</span>
          </div>
        </div>

        <div className={styles.panel}>
          <h3 className={styles.panelTitle}>Breakdown by Instrument</h3>
          {(hasDebtData ? debtData.by_instrument : KNOWN_DEBT.instruments.map(i => ({
            instrument: i.name, face_value_aud: i.amount, as_at: KNOWN_DEBT.asAt, note: i.note,
          }))).map((r, i) => {
            const pct = Math.round((r.face_value_aud / debtTotal) * 100);
            return (
              <div key={i} className={styles.debtRow}>
                <div className={styles.debtLeft}>
                  <span className={styles.debtName}>{r.instrument}</span>
                  {r.note && <span className={styles.debtNote}>{r.note}</span>}
                </div>
                <div className={styles.debtBarWrap}>
                  <div className={styles.debtBar} style={{ width: `${pct}%` }} />
                </div>
                <span className={styles.debtAmt}>{fmtB(r.face_value_aud)}</span>
                <span className={styles.debtPct}>{pct}%</span>
              </div>
            );
          })}
        </div>

        <div className={styles.panel}>
          <h3 className={styles.panelTitle}>Context</h3>
          <ul className={styles.contextList}>
            <li>The Commonwealth issues bonds to fund spending when revenue is less than expenditure (deficit financing).</li>
            <li>Treasury Bonds are the primary instrument — long-term, fixed rate, bought by superannuation funds, banks, and foreign investors.</li>
            <li>The RBA holds a significant portion from its 2020–21 bond purchase program (quantitative easing).</li>
            <li>Net debt (gross minus financial assets) is lower — around $600B — because the government holds assets including HECS receivables, future fund, etc.</li>
            <li>Australia's debt-to-GDP ratio (~40%) is low by international standards (US ~120%, Japan ~250%).</li>
          </ul>
          <p className={styles.sourceNote}>
            Source: <a href={KNOWN_DEBT.sourceUrl} target="_blank" rel="noreferrer">{KNOWN_DEBT.source}</a>
            {!hasDebtData && (
              <span className={styles.fetchHint}>
                {' '}— run <code>fetch_debt.py</code> + <code>parse_debt.py</code> to load live data.
              </span>
            )}
          </p>
        </div>
      </section>

      {/* ── HECS/HELP ── */}
      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <h2 className={styles.heading}>HECS / HELP Student Loan Book</h2>
          <span className={styles.sub}>Higher Education Loan Program — who owes what, and what comes back</span>
        </div>

        <div className={styles.statRow}>
          <div className={styles.bigStat}>
            <span className={styles.bigLabel}>Total Outstanding</span>
            <span className={styles.bigVal} style={{ color: '#d29922' }}>{fmtB(hecsOutstanding)}</span>
            <span className={styles.bigNote}>
              {hasHecsData ? 'Live from database' : 'Context figure — Dept of Education 2023'}
            </span>
          </div>
          <div className={styles.bigStat}>
            <span className={styles.bigLabel}>Active Debtors</span>
            <span className={styles.bigVal}>{KNOWN_HECS.borrowers.toLocaleString()}</span>
            <span className={styles.bigNote}>~3.2 million Australians with HELP debt</span>
          </div>
          <div className={styles.bigStat}>
            <span className={styles.bigLabel}>Average Debt</span>
            <span className={styles.bigVal}>${KNOWN_HECS.avg_debt.toLocaleString()}</span>
            <span className={styles.bigNote}>Per debtor — rising year on year</span>
          </div>
        </div>

        <div className={styles.twoCol}>
          <div className={styles.panel}>
            <h3 className={styles.panelTitle}>Annual flows</h3>
            {[
              { label: 'New loans issued per year',         val: KNOWN_HECS.annual_new_loans,  color: '#f85149', note: 'FEE-HELP, HECS-HELP, VET Student Loans' },
              { label: 'Repayments collected (ATO)',        val: KNOWN_HECS.annual_repayments, color: '#3fb950', note: 'Compulsory + voluntary via tax system' },
              { label: 'Written off annually',              val: KNOWN_HECS.write_offs,        color: '#8b949e', note: 'Deaths, permanent incapacity, no-tax-file' },
            ].map((r, i) => (
              <div key={i} className={styles.hecsRow}>
                <div className={styles.hecsLeft}>
                  <span className={styles.hecsLabel}>{r.label}</span>
                  <span className={styles.hecsNote}>{r.note}</span>
                </div>
                <span className={styles.hecsAmt} style={{ color: r.color }}>{fmtB(r.val)}</span>
              </div>
            ))}
            <p className={styles.hecsGap}>
              Net increase each year: <strong style={{color:'#f85149'}}>{fmtB(KNOWN_HECS.annual_new_loans - KNOWN_HECS.annual_repayments - KNOWN_HECS.write_offs)}</strong> before indexation.
            </p>
          </div>

          <div className={styles.panel}>
            <h3 className={styles.panelTitle}>CPI Indexation applied to all debts</h3>
            {[
              { year: '2023 (Jun)', rate: KNOWN_HECS.indexation_2023, note: 'Added ~$3.5B to total debt stock' },
              { year: '2024 (Jun)', rate: KNOWN_HECS.indexation_2024, note: 'Partial cap legislated after public pressure' },
              { year: '2025 (Jun)', rate: null,                        note: 'Rate TBC — tied to CPI or wage growth' },
            ].map((r, i) => (
              <div key={i} className={styles.indexRow}>
                <span className={styles.indexYear}>{r.year}</span>
                <span className={styles.indexRate} style={{ color: r.rate > 5 ? '#f85149' : '#d29922' }}>
                  {r.rate != null ? `+${r.rate}%` : '—'}
                </span>
                <span className={styles.indexNote}>{r.note}</span>
              </div>
            ))}
            <p className={styles.hecsGap}>
              Indexation is applied to the entire loan book each June — meaning even borrowers making repayments can see their debt grow if repayments don't outpace CPI.
            </p>
          </div>
        </div>

        <div className={styles.panel}>
          <h3 className={styles.panelTitle}>Why the debt keeps growing</h3>
          <ul className={styles.contextList}>
            <li><strong>More students borrowing:</strong> ~$11B in new loans issued each year vs ~$5B repaid.</li>
            <li><strong>Low repayment threshold earners:</strong> Graduates earning under the repayment threshold (~$51K) make no repayments while interest accrues.</li>
            <li><strong>Part-time / career gap borrowers:</strong> Many borrowers take years to reach repayment threshold.</li>
            <li><strong>CPI indexation:</strong> Applied annually to the entire stock, even where repayments are being made — 7.1% in 2023 added ~$3.5B overnight.</li>
            <li><strong>Write-offs are small:</strong> Only ~$400M/year is written off, even though a large portion may never be fully repaid.</li>
          </ul>
          <p className={styles.sourceNote}>
            Source: <a href={KNOWN_HECS.sourceUrl} target="_blank" rel="noreferrer">{KNOWN_HECS.source}</a>
            {!hasHecsData && (
              <span className={styles.fetchHint}>
                {' '}— run <code>fetch_debt.py</code> + <code>parse_debt.py</code> for live data.
              </span>
            )}
          </p>
        </div>
      </section>

    </div>
  );
}
