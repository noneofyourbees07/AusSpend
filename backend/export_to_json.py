"""
Export the SQLite database to static JSON files.

GitHub Pages can only host static files (no Python). Instead of running
Flask in production, we pre-bake the data into JSON at build time and
the React app reads those files directly.

Run this whenever you update the database:
    python3 export_to_json.py

Output goes to ../public/data/ which Vite includes in the build.
"""
import os
import json
import sqlite3

from db import get_conn

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'data')


def write_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w') as f:
        json.dump(data, f, separators=(',', ':'))   # compact, no whitespace
    size_kb = os.path.getsize(path) / 1024
    print(f'  ✓ {filename}  ({size_kb:.0f} KB, {len(data) if isinstance(data, list) else "object"})')


def export_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = get_conn()
    conn.row_factory = sqlite3.Row

    print('\n── Exporting to JSON ──')

    # ── Sector totals (combined spending + contracts) ──
    rows = conn.execute('''
        SELECT sector, SUM(total) as total, SUM(cnt) as cnt FROM (
            SELECT sector, SUM(amount_aud) as total, COUNT(*) as cnt
            FROM spending GROUP BY sector
            UNION ALL
            SELECT sector, SUM(value_aud) as total, COUNT(*) as cnt
            FROM contracts GROUP BY sector
        ) combined
        GROUP BY sector
        ORDER BY total DESC
    ''').fetchall()
    write_json('sectors_all.json', [
        {'sector': r['sector'], 'total_aud': r['total'], 'program_count': r['cnt']}
        for r in rows
    ])

    # ── Sectors per year (for year filter) ──
    # Pre-compute every year so the client can pick instantly
    by_year = {}
    rows = conn.execute('''
        SELECT year, sector, SUM(total) as total, SUM(cnt) as cnt FROM (
            SELECT year, sector, SUM(amount_aud) as total, COUNT(*) as cnt
            FROM spending WHERE year != '' GROUP BY year, sector
            UNION ALL
            SELECT year, sector, SUM(value_aud) as total, COUNT(*) as cnt
            FROM contracts WHERE year != '' GROUP BY year, sector
        ) combined
        GROUP BY year, sector
    ''').fetchall()
    for r in rows:
        by_year.setdefault(r['year'], []).append({
            'sector': r['sector'],
            'total_aud': r['total'],
            'program_count': r['cnt'],
        })
    # Sort each year's list by total DESC
    for yr in by_year:
        by_year[yr].sort(key=lambda x: -(x['total_aud'] or 0))
    write_json('sectors_by_year.json', by_year)

    # ── Year-on-year summary (feeds the bar charts) ──
    summary = {}
    rows = conn.execute('''
        SELECT sector, year, SUM(amount_aud) as total
        FROM spending WHERE year != ''
        GROUP BY sector, year
    ''').fetchall()
    for r in rows:
        summary.setdefault(r['sector'], {})[r['year']] = r['total']
    write_json('summary.json', summary)

    # ── All spending records (only ~23K — manageable client-side) ──
    rows = conn.execute('''
        SELECT id, entity, program, sector, year, amount_aud, source_file
        FROM spending
        ORDER BY ABS(amount_aud) DESC
    ''').fetchall()
    write_json('spending.json', [
        {
            'id': r['id'],
            'entity': r['entity'],
            'program': r['program'],
            'sector': r['sector'],
            'year': r['year'],
            'amount_aud': r['amount_aud'],
            'source_file': r['source_file'],
        }
        for r in rows
    ])

    # ── Top contracts per sector (limit to keep file size sane) ──
    # Full contracts table is ~50MB JSON. We export top 500 per sector instead.
    sectors = [r['sector'] for r in conn.execute('SELECT DISTINCT sector FROM contracts').fetchall()]
    contracts_by_sector = {}
    contract_counts = {}
    for sector in sectors:
        rows = conn.execute('''
            SELECT cn_id, agency, supplier, description, value_aud,
                   start_date, end_date, category, sector, state, year
            FROM contracts WHERE sector = ?
            ORDER BY value_aud DESC LIMIT 500
        ''', (sector,)).fetchall()
        contracts_by_sector[sector] = [dict(r) for r in rows]

        # Total count for badge
        cnt = conn.execute('SELECT COUNT(*) FROM contracts WHERE sector = ?', (sector,)).fetchone()[0]
        contract_counts[sector] = cnt

    write_json('contracts_top.json', contracts_by_sector)
    write_json('contracts_counts.json', contract_counts)

    # ── Revenue ──
    rows = conn.execute('''
        SELECT category, subcategory, year, SUM(amount_aud) as total
        FROM revenue
        GROUP BY category, subcategory, year
        ORDER BY total DESC
    ''').fetchall()
    by_cat = [dict(r) for r in rows]
    for r in by_cat:
        r['total_aud'] = r.pop('total')

    rows = conn.execute('''
        SELECT year, SUM(amount_aud) as total
        FROM revenue
        GROUP BY year ORDER BY year
    ''').fetchall()
    by_yr = [{'year': r['year'], 'total_aud': r['total']} for r in rows]

    write_json('revenue.json', {
        'by_category': by_cat,
        'by_year': by_yr,
    })

    # ── Sources ──
    spending_sources = conn.execute('''
        SELECT s.source_file as file, d.title as dataset_title, d.url as dataset_url,
               COUNT(s.id) as records, MIN(s.year) as year_from, MAX(s.year) as year_to
        FROM spending s LEFT JOIN datasets d ON s.dataset_id = d.id
        GROUP BY s.source_file ORDER BY records DESC
    ''').fetchall()
    revenue_sources = conn.execute('''
        SELECT source_file as file, COUNT(*) as records
        FROM revenue GROUP BY source_file ORDER BY records DESC
    ''').fetchall()
    write_json('sources.json', {
        'spending': [dict(r) for r in spending_sources],
        'revenue':  [dict(r) for r in revenue_sources],
    })

    # ── Debt (live data if we ever have it) ──
    debt_count = conn.execute('SELECT COUNT(*) FROM national_debt').fetchone()[0]
    if debt_count > 0:
        by_inst = conn.execute('''
            SELECT instrument, face_value_aud, date as as_at
            FROM national_debt nd1
            WHERE date = (SELECT MAX(date) FROM national_debt nd2 WHERE nd2.instrument = nd1.instrument)
            ORDER BY face_value_aud DESC
        ''').fetchall()
        timeseries = conn.execute('''
            SELECT date, SUM(face_value_aud) as total_aud
            FROM national_debt GROUP BY date ORDER BY date
        ''').fetchall()
        write_json('debt.json', {
            'record_count': debt_count,
            'by_instrument': [dict(r) for r in by_inst],
            'timeseries':    [dict(r) for r in timeseries],
        })
    else:
        write_json('debt.json', {'record_count': 0, 'by_instrument': [], 'timeseries': []})

    # ── HECS (live data if we ever have it) ──
    hecs_count = conn.execute('SELECT COUNT(*) FROM hecs_debt').fetchone()[0]
    write_json('hecs.json', {'record_count': hecs_count, 'by_year': [], 'outstanding_trend': []})

    conn.close()
    print(f'\n✓ Done. JSON files written to {OUTPUT_DIR}')


if __name__ == '__main__':
    export_all()
