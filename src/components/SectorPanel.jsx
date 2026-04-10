import { useState, useEffect } from 'react';
import { SECTORS } from '../data';
import NoData from './NoData';
import styles from './SectorPanel.module.css';

function fmtAmt(val) {
  if (val == null) return null;
  const abs = Math.abs(val);
  if (abs >= 1_000_000_000) return `$${(val / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000)     return `$${(val / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000)         return `$${(val / 1_000).toFixed(0)}K`;
  return `$${val.toFixed(0)}`;
}

function stripHtml(str) {
  return str?.replace(/<[^>]*>/g, '').trim() || '';
}

export default function SectorPanel({ activeSector, onSectorChange, search, sectorTotal, year, state }) {
  const [view,      setView]      = useState('budget');   // 'budget' | 'contracts'
  const [programs,  setPrograms]  = useState([]);
  const [contracts, setContracts] = useState([]);
  const [contractTotal, setContractTotal] = useState(0);
  const [loading,   setLoading]   = useState(false);

  const sector = SECTORS[activeSector];

  // Reset view when switching sector
  useEffect(() => { setView('budget'); }, [activeSector]);

  // Fetch budget programs
  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ sector: activeSector, limit: 25 });
    if (search) params.set('search', search);
    if (year)   params.set('year', year);
    fetch(`/api/spending?${params}`)
      .then(r => r.json())
      .then(data => setPrograms(data.results ?? []))
      .catch(() => setPrograms([]))
      .finally(() => setLoading(false));
  }, [activeSector, search, year]);

  // Fetch contracts when switching to contracts view (or filters change)
  useEffect(() => {
    if (view !== 'contracts') return;
    setLoading(true);
    const params = new URLSearchParams({ sector: activeSector, limit: 50 });
    if (search) params.set('search', search);
    if (year)   params.set('year', year);
    if (state)  params.set('state', state);
    fetch(`/api/contracts?${params}`)
      .then(r => r.json())
      .then(data => {
        setContracts(data.results ?? []);
        setContractTotal(data.total ?? 0);
      })
      .catch(() => setContracts([]))
      .finally(() => setLoading(false));
  }, [view, activeSector, search, year, state]);

  // Also fetch contract count on mount so the badge shows even before clicking
  useEffect(() => {
    const params = new URLSearchParams({ sector: activeSector, limit: 1 });
    if (year)  params.set('year', year);
    if (state) params.set('state', state);
    fetch(`/api/contracts?${params}`)
      .then(r => r.json())
      .then(data => setContractTotal(data.total ?? 0))
      .catch(() => {});
  }, [activeSector, year, state]);

  return (
    <div className={styles.panel}>

      {/* Sector tabs */}
      <div className={styles.tabs}>
        {Object.entries(SECTORS).map(([key, s]) => (
          <button
            key={key}
            className={`${styles.tab} ${activeSector === key ? styles.active : ''}`}
            style={activeSector === key ? { borderBottomColor: s.color, color: s.color } : {}}
            onClick={() => onSectorChange(key)}
          >
            {s.label.split(' ')[0]}
          </button>
        ))}
      </div>

      {/* Heading */}
      <div className={styles.heading}>
        <div>
          <h2 className={styles.sectorTitle}>{sector.label}</h2>
          {year && (
            <span className={styles.yearBadge}>
              {year}-{(parseInt(year) + 1).toString().slice(-2)}
            </span>
          )}
        </div>
        <span className={styles.sectorTotal} style={{ color: sector.color }}>
          {fmtAmt(sectorTotal) ?? '— awaiting data'}
        </span>
      </div>
      <p className={styles.desc}>{sector.desc}</p>

      {/* View switcher */}
      <div className={styles.viewBar}>
        <button
          className={`${styles.viewBtn} ${view === 'budget' ? styles.viewActive : ''}`}
          onClick={() => setView('budget')}
        >
          Budget programs
        </button>
        <button
          className={`${styles.viewBtn} ${view === 'contracts' ? styles.viewActive : ''}`}
          onClick={() => setView('contracts')}
        >
          Individual contracts
          {contractTotal > 0 && <span className={styles.countBadge}>{contractTotal.toLocaleString()}</span>}
        </button>
        {view === 'contracts' && contracts.length === 0 && !loading && (
          <span className={styles.noContractsHint}>Run fetch_contracts.py to load AusTender data</span>
        )}
      </div>

      {/* Budget programs table */}
      {view === 'budget' && (
        loading ? (
          <p className={styles.empty}>Loading…</p>
        ) : programs.length === 0 ? (
          <NoData year={year} reason={year ? 'year' : 'filter'} compact />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Program / Description</th>
                  <th>Agency</th>
                  <th className={styles.num}>Year</th>
                  <th className={styles.num}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {programs.map(p => {
                  const maxAmt = Math.max(...programs.map(r => Math.abs(r.amount_aud ?? 0)), 1);
                  const barPct = Math.round((Math.abs(p.amount_aud ?? 0) / maxAmt) * 80);
                  return (
                    <tr key={p.id}>
                      <td><span className={styles.programName}>{p.program || '—'}</span></td>
                      <td><span className={styles.agencyName}>{p.entity || '—'}</span></td>
                      <td className={styles.num}>
                        <span className={styles.yearVal}>{p.year || '—'}</span>
                      </td>
                      <td className={styles.num}>
                        <div className={styles.shareWrap}>
                          <div
                            className={styles.shareBar}
                            style={{ width: `${barPct}px`, background: sector.color + '55', borderColor: sector.color }}
                          />
                          <span className={styles.amount}>{fmtAmt(p.amount_aud) ?? '—'}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className={styles.tableNote}>
              Budget program level — broad outcomes/outputs. Switch to <strong>Individual contracts</strong> for project detail.
            </p>
          </div>
        )
      )}

      {/* Contracts table */}
      {view === 'contracts' && (
        loading ? (
          <p className={styles.empty}>Loading…</p>
        ) : contracts.length === 0 ? (
          <NoData year={year} reason={year ? 'year' : 'filter'} compact />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Description</th>
                  <th>Supplier</th>
                  <th>Agency</th>
                  <th title="The financial year a contract is filed under is when it was published — but the actual delivery period can span several years. Hover over a date to see the full range.">
                    Dates <span className={styles.headHint}>?</span>
                  </th>
                  <th className={styles.num}>State</th>
                  <th className={styles.num}>Value</th>
                </tr>
              </thead>
              <tbody>
                {contracts.map((c, i) => (
                  <tr key={i}>
                    <td><span className={styles.programName}>{stripHtml(c.description) || '—'}</span>
                        {c.category && <span className={styles.contractCat}>{c.category}</span>}
                    </td>
                    <td><span className={styles.agencyName}>{c.supplier || '—'}</span></td>
                    <td><span className={styles.agencyName}>{c.agency || '—'}</span></td>
                    <td title={c.start_date && c.end_date ? `Contract filed FY ${c.year} · runs ${c.start_date} → ${c.end_date}. Multi-year contracts are common — the filing year is just when it was published.` : ''}>
                      <span className={styles.dateVal}>{c.start_date || '—'}</span>
                      {c.end_date && <span className={styles.dateTo}> → {c.end_date}</span>}
                    </td>
                    <td className={styles.num}><span className={styles.yearVal}>{c.state || '—'}</span></td>
                    <td className={styles.num}>
                      <span className={styles.amount}>{fmtAmt(c.value_aud) ?? '—'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className={styles.tableNote}>
              Top 50 by value · {contractTotal.toLocaleString()} total contracts in this sector. Source: AusTender.
              <br />
              <span className={styles.footnoteHint}>
                ⓘ The year filter shows when a contract was <em>published</em>. The
                actual delivery period (start → end dates) often spans multiple years —
                e.g. a 2017 contract may be delivering work through 2024.
              </span>
            </p>
          </div>
        )
      )}
    </div>
  );
}
