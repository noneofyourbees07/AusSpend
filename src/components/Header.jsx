import { useState, useEffect } from 'react';
import styles from './Header.module.css';

const NAV = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'spending',  label: 'Spending' },
  { id: 'revenue',   label: 'Revenue' },
  { id: 'debt',      label: 'Debt' },
  { id: 'scope',     label: 'Data Scope' },
  { id: 'sources',   label: 'Sources' },
];

export default function Header({ page, onNavigate, year, onYearChange }) {
  const [menuOpen, setMenuOpen] = useState(false);

  // Close menu when navigating
  function handleNav(id) {
    onNavigate(id);
    setMenuOpen(false);
  }

  // Close menu on Escape
  useEffect(() => {
    if (!menuOpen) return;
    const onKey = e => { if (e.key === 'Escape') setMenuOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [menuOpen]);

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.logo} onClick={() => handleNav('dashboard')}>
          <span className={styles.logoIcon}>$</span>
          <div>
            <span className={styles.logoTitle}>AusSpend</span>
            <span className={styles.logoSub}>Australian Government Spending Tracker</span>
          </div>
        </div>

        {/* Desktop nav */}
        <nav className={styles.nav}>
          {NAV.map(n => (
            <button
              key={n.id}
              className={`${styles.navBtn} ${page === n.id ? styles.navActive : ''}`}
              onClick={() => handleNav(n.id)}
            >
              {n.label}
            </button>
          ))}
        </nav>

        <div className={styles.meta}>
          <select
            className={styles.select}
            value={year}
            onChange={e => onYearChange(e.target.value)}
          >
            <option value="">All years</option>
            <option value="2026">2025–26 (current)</option>
            <option value="2025">2024–25</option>
            <option value="2024">2023–24</option>
            <option value="2023">2022–23</option>
            <option value="2022">2021–22</option>
            <option value="2021">2020–21</option>
            <option value="2019">2019–20</option>
            <option value="2018">2018–19</option>
            <option value="2017">2017–18</option>
            <option value="2016">2016–17</option>
            <option value="2015">2015–16</option>
            <option value="2014">2014–15</option>
          </select>
          <span className={styles.badge}>data.gov.au</span>

          {/* Mobile hamburger button */}
          <button
            className={styles.hamburger}
            onClick={() => setMenuOpen(o => !o)}
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
          >
            <span className={`${styles.hamburgerBar} ${menuOpen ? styles.barTop : ''}`}></span>
            <span className={`${styles.hamburgerBar} ${menuOpen ? styles.barMid : ''}`}></span>
            <span className={`${styles.hamburgerBar} ${menuOpen ? styles.barBot : ''}`}></span>
          </button>
        </div>
      </div>

      {/* Mobile drop-down menu */}
      {menuOpen && (
        <>
          <div className={styles.backdrop} onClick={() => setMenuOpen(false)} />
          <nav className={styles.mobileNav}>
            {NAV.map(n => (
              <button
                key={n.id}
                className={`${styles.mobileBtn} ${page === n.id ? styles.mobileActive : ''}`}
                onClick={() => handleNav(n.id)}
              >
                {n.label}
              </button>
            ))}
          </nav>
        </>
      )}
    </header>
  );
}
