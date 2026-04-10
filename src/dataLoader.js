// ============================================================
// Static data loader
// All API calls go through here so we can swap source easily.
// In production these are static JSON files baked into the build.
// ============================================================

// Vite injects BASE_URL based on vite.config.js `base` setting.
// In dev it's '/', on GitHub Pages it's '/AusSpend/'.
const BASE = import.meta.env.BASE_URL;

function dataUrl(file) {
  return `${BASE}data/${file}`;
}

// Cache so we don't re-fetch the same JSON multiple times in a session.
const cache = new Map();

async function loadJson(file) {
  if (cache.has(file)) return cache.get(file);
  const promise = fetch(dataUrl(file)).then(r => {
    if (!r.ok) throw new Error(`Failed to load ${file}: ${r.status}`);
    return r.json();
  });
  cache.set(file, promise);
  return promise;
}

// ── Public API (matches the old Flask endpoints) ──

export async function fetchSectors(year) {
  if (!year) {
    return loadJson('sectors_all.json');
  }
  // Year-filtered: convert dropdown year (e.g. "2024") to FY string ("2023-24")
  const yr = parseInt(year);
  const fy = `${yr - 1}-${String(yr).slice(2)}`;
  const all = await loadJson('sectors_by_year.json');
  return all[fy] ?? [];
}

export async function fetchSummary() {
  return loadJson('summary.json');
}

export async function fetchRevenue(year) {
  const data = await loadJson('revenue.json');
  if (!year) return data;
  const yr = parseInt(year);
  const fy = `${yr - 1}-${String(yr).slice(2)}`;
  return {
    by_category: data.by_category.filter(r => r.year === fy),
    by_year:     data.by_year.filter(r => r.year === fy),
  };
}

export async function fetchSpending({ sector, year, search, limit = 25 } = {}) {
  const all = await loadJson('spending.json');
  let rows = all;

  if (sector) rows = rows.filter(r => r.sector === sector);

  if (year) {
    const yr = parseInt(year);
    const fy = `${yr - 1}-${String(yr).slice(2)}`;
    rows = rows.filter(r => r.year === fy);
  }

  if (search) {
    const q = search.toLowerCase();
    rows = rows.filter(r =>
      (r.entity ?? '').toLowerCase().includes(q) ||
      (r.program ?? '').toLowerCase().includes(q)
    );
  }

  return {
    total: rows.length,
    results: rows.slice(0, limit),
  };
}

export async function fetchContracts({ sector, year, search, state, limit = 50 } = {}) {
  const bySector = await loadJson('contracts_top.json');
  const counts   = await loadJson('contracts_counts.json');

  let rows = sector ? (bySector[sector] ?? []) : Object.values(bySector).flat();

  if (year) {
    const yr = parseInt(year);
    const fy = `${yr - 1}-${String(yr).slice(2)}`;
    rows = rows.filter(r => r.year === fy);
  }

  if (state) {
    rows = rows.filter(r => r.state === state);
  }

  if (search) {
    const q = search.toLowerCase();
    rows = rows.filter(r =>
      (r.description ?? '').toLowerCase().includes(q) ||
      (r.supplier ?? '').toLowerCase().includes(q) ||
      (r.agency ?? '').toLowerCase().includes(q)
    );
  }

  return {
    total: sector ? (counts[sector] ?? rows.length) : rows.length,
    results: rows.slice(0, limit),
  };
}

export async function fetchSources() {
  return loadJson('sources.json');
}

export async function fetchDebt() {
  return loadJson('debt.json');
}

export async function fetchHecs() {
  return loadJson('hecs.json');
}
