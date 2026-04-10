import styles from './NoData.module.css';

/**
 * Reusable "no data" panel — explains why data is missing
 * and what the user can do about it.
 *
 * Props:
 *   year      — the year that was filtered (optional)
 *   reason    — 'year' (no data for this year) | 'empty' (no data at all) | 'filter' (filters too narrow)
 *   compact   — smaller version for tables/sidebars
 */
export default function NoData({ year, reason = 'year', compact = false }) {
  const yearLabel = year ? `${year}-${(parseInt(year) + 1).toString().slice(-2)}` : '';

  let title, body;

  if (reason === 'year') {
    title = `No data available for ${yearLabel}`;
    body = (
      <>
        <p>
          The Australian government publishes spending data through{' '}
          <a href="https://data.gov.au" target="_blank" rel="noreferrer">data.gov.au</a>,
          but the AusTender contract exports on that portal have <strong>not been
          updated since 2019</strong>. This is a known issue with the open data portal —
          the source systems are still being updated, but the convenient bulk
          downloads have gone stale.
        </p>
        <p className={styles.dim}>
          Try selecting a year between <strong>2014–15 and 2018–19</strong> to see
          full data, or switch to <strong>All years</strong>.
        </p>
        <p className={styles.dim}>
          We&rsquo;re working on pulling fresh data directly from{' '}
          <a href="https://tenders.gov.au" target="_blank" rel="noreferrer">tenders.gov.au</a>{' '}
          and the annual Budget Papers to fill the 2020+ gap.
        </p>
      </>
    );
  } else if (reason === 'filter') {
    title = 'No results for these filters';
    body = (
      <p>Try removing the search term, state, or sector filter — or click <strong>Clear</strong> to reset.</p>
    );
  } else {
    title = 'No data loaded';
    body = (
      <p>
        Run the backend ingest scripts in <code>backend/</code> to populate the database.
        See <code>README</code> for instructions.
      </p>
    );
  }

  return (
    <div className={`${styles.box} ${compact ? styles.compact : ''}`}>
      <div className={styles.icon}>!</div>
      <div className={styles.content}>
        <h3 className={styles.title}>{title}</h3>
        <div className={styles.body}>{body}</div>
      </div>
    </div>
  );
}
