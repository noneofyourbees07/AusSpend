import { SECTORS } from '../data';
import styles from './FilterBar.module.css';

export default function FilterBar({ search, sector, state, onSearch, onSector, onState, onClear }) {
  return (
    <div className={styles.bar}>
      <input
        className={styles.input}
        type="text"
        placeholder="Search programs, agencies, sectors..."
        value={search}
        onChange={e => onSearch(e.target.value)}
      />
      <select
        className={styles.select}
        value={sector}
        onChange={e => onSector(e.target.value)}
      >
        <option value="">All Sectors</option>
        {Object.entries(SECTORS).map(([key, s]) => (
          <option key={key} value={key}>{s.label}</option>
        ))}
      </select>
      <select
        className={styles.select}
        value={state}
        onChange={e => onState(e.target.value)}
      >
        <option value="">All States</option>
        {['NSW','VIC','QLD','WA','SA','TAS','ACT','NT'].map(s => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
      <button className={styles.clear} onClick={onClear}>Clear</button>
    </div>
  );
}
