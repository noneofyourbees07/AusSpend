import styles from './NewsPanel.module.css';

export default function NewsPanel({ sector }) {
  const news = sector.news ?? [];

  return (
    <div className={styles.panel}>
      <h3 className={styles.title}>
        News &amp; Context <span className={styles.sub}>— recent coverage</span>
      </h3>
      {news.length === 0 ? (
        <p className={styles.empty}>No news context loaded yet. Enrichment layer coming soon.</p>
      ) : (
        <ul className={styles.list}>
          {news.map((n, i) => (
            <li key={i} className={styles.item}>
              <span className={styles.headline}>{n.headline}</span>
              <span className={styles.meta}>
                <span>{n.source}</span>
                <span>{n.date}</span>
                {n.tags.map(t => (
                  <span key={t} className={styles.tag}>{t}</span>
                ))}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
