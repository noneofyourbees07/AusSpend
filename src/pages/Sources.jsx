import { useState, useEffect } from 'react';
import { fetchSources } from '../dataLoader';
import styles from './Sources.module.css';

export default function Sources() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSources()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className={styles.empty}>Loading sources…</div>;
  if (!data)   return <div className={styles.empty}>Could not load source data.</div>;

  return (
    <div className={styles.page}>
      <div className={styles.intro}>
        <h2 className={styles.heading}>Data Sources</h2>
        <p className={styles.sub}>
          Every number on this site comes from one of these files. Click the dataset link
          to open the original record on data.gov.au and verify the numbers yourself.
          We do not modify the source data — only classify and aggregate it.
        </p>
      </div>

      <div className={styles.panel}>
        <h3 className={styles.sectionTitle}>Spending Sources ({data.spending.length} files)</h3>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>File</th>
                <th>Dataset (data.gov.au)</th>
                <th className={styles.num}>Records</th>
                <th>Years covered</th>
              </tr>
            </thead>
            <tbody>
              {data.spending.map((s, i) => (
                <tr key={i}>
                  <td><code className={styles.code}>{s.file}</code></td>
                  <td>
                    {s.dataset_url ? (
                      <a href={s.dataset_url} target="_blank" rel="noreferrer" className={styles.link}>
                        {s.dataset_title || s.dataset_url}
                      </a>
                    ) : (
                      <span className={styles.dim}>{s.dataset_title || '—'}</span>
                    )}
                  </td>
                  <td className={styles.num}>{s.records?.toLocaleString()}</td>
                  <td className={styles.dim}>
                    {s.year_from && s.year_to
                      ? s.year_from === s.year_to ? s.year_from : `${s.year_from} – ${s.year_to}`
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.revenue.length > 0 && (
        <div className={styles.panel}>
          <h3 className={styles.sectionTitle}>Revenue Sources ({data.revenue.length} files)</h3>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>File</th>
                  <th className={styles.num}>Records</th>
                </tr>
              </thead>
              <tbody>
                {data.revenue.map((r, i) => (
                  <tr key={i}>
                    <td><code className={styles.code}>{r.file}</code></td>
                    <td className={styles.num}>{r.records?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className={styles.panel}>
        <h3 className={styles.sectionTitle}>How the data is processed</h3>
        <ol className={styles.steps}>
          <li>Files are downloaded from <a href="https://data.gov.au" target="_blank" rel="noreferrer">data.gov.au</a> via their official CKAN API — no scraping.</li>
          <li>CSVs and Excel files are parsed column-by-column. Rows with no numeric amount are skipped.</li>
          <li>Each row is classified into a sector (Health, Welfare, etc.) using keyword matching against the program name and entity name.</li>
          <li>Duplicate rows are detected by hashing entity + program + year + amount and skipped on re-import.</li>
          <li>Nothing is modified — dollar amounts are stored exactly as they appear in the source file.</li>
        </ol>
        <p className={styles.caveat}>
          <strong>Limitations:</strong> Government datasets use inconsistent column names, financial years, and units
          (some files use $thousands, others $millions). Amounts shown may be incomplete until more datasets are ingested.
          Always verify large figures against the original source document.
        </p>
      </div>
    </div>
  );
}
