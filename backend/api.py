"""
Flask API — serves spending data to the React frontend.

Run: python3 api.py
Endpoints:
  GET /api/spending          — all records (paginated)
  GET /api/spending/summary  — totals per sector per year
  GET /api/sectors           — list of sectors + totals
  GET /api/health            — liveness check
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

from db import get_conn

app = Flask(__name__)
CORS(app)   # allow the React dev server (localhost:5173) to call this API


def to_fy(year_str):
    """Convert dropdown year (e.g. '2024') to financial year format '2023-24'.
    Returns None if empty/invalid."""
    if not year_str:
        return None
    try:
        yr = int(year_str)
        return f'{yr-1}-{str(yr)[2:]}'
    except ValueError:
        return None


# ── Health ────────────────────────────────────────────────────────────────────

@app.get('/api/health')
def health():
    return jsonify({'status': 'ok'})


# ── Sector summary ────────────────────────────────────────────────────────────

@app.get('/api/sectors')
def sectors():
    """Return total spending per sector, optionally filtered by year.
    Combines spending + contracts tables for a fuller picture."""
    fy = to_fy(request.args.get('year'))
    conn = get_conn()

    if fy:
        # Combine spending + contracts for year-filtered view
        rows = conn.execute('''
            SELECT sector, SUM(total) as total, SUM(cnt) as cnt FROM (
                SELECT sector, SUM(amount_aud) as total, COUNT(*) as cnt
                FROM spending WHERE year = ?
                GROUP BY sector
                UNION ALL
                SELECT sector, SUM(value_aud) as total, COUNT(*) as cnt
                FROM contracts WHERE year = ?
                GROUP BY sector
            ) combined
            GROUP BY sector
            ORDER BY total DESC
        ''', (fy, fy)).fetchall()
    else:
        # All years — spending totals + contract counts
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

    conn.close()
    return jsonify([
        {'sector': r[0], 'total_aud': r[1], 'program_count': r[2]}
        for r in rows
    ])


# ── Spending records ──────────────────────────────────────────────────────────

@app.get('/api/spending')
def spending():
    """
    Return spending records with optional filters.
    Query params: sector, year, entity, search, limit, offset
    """
    sector = request.args.get('sector')
    fy     = to_fy(request.args.get('year'))
    entity = request.args.get('entity')
    search = request.args.get('search')
    limit  = min(int(request.args.get('limit',  200)), 1000)
    offset = int(request.args.get('offset', 0))

    where  = []
    params = []

    if sector:
        where.append('sector = ?')
        params.append(sector)
    if fy:
        where.append('year = ?')
        params.append(fy)
    if entity:
        where.append('entity LIKE ?')
        params.append(f'%{entity}%')
    if search:
        where.append('(entity LIKE ? OR program LIKE ?)')
        params += [f'%{search}%', f'%{search}%']

    where_clause = ('WHERE ' + ' AND '.join(where)) if where else ''

    conn  = get_conn()
    rows  = conn.execute(f'''
        SELECT id, entity, program, sector, year, amount_aud, source_file
        FROM spending
        {where_clause}
        ORDER BY ABS(amount_aud) DESC
        LIMIT ? OFFSET ?
    ''', params + [limit, offset]).fetchall()

    total = conn.execute(f'''
        SELECT COUNT(*) FROM spending {where_clause}
    ''', params).fetchone()[0]

    conn.close()

    return jsonify({
        'total':   total,
        'limit':   limit,
        'offset':  offset,
        'results': [
            {
                'id':          r[0],
                'entity':      r[1],
                'program':     r[2],
                'sector':      r[3],
                'year':        r[4],
                'amount_aud':  r[5],
                'source_file': r[6],
            }
            for r in rows
        ],
    })


# ── Year-on-year summary ──────────────────────────────────────────────────────

@app.get('/api/spending/summary')
def summary():
    """Return year-on-year totals per sector — feeds the bar charts."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT sector, year, SUM(amount_aud) as total
        FROM spending
        GROUP BY sector, year
        ORDER BY sector, year
    ''').fetchall()
    conn.close()

    # Reshape into {sector: {year: total}}
    result = {}
    for sector, year, total in rows:
        if sector not in result:
            result[sector] = {}
        result[sector][year] = total

    return jsonify(result)


# ── Data sources ─────────────────────────────────────────────────────────────

@app.get('/api/sources')
def sources():
    """Return distinct source files + their dataset metadata."""
    conn = get_conn()

    # Spending sources: source file + dataset title + url + record count
    rows = conn.execute('''
        SELECT s.source_file,
               d.title,
               d.url,
               COUNT(s.id) as record_count,
               MIN(s.year) as year_from,
               MAX(s.year) as year_to
        FROM spending s
        LEFT JOIN datasets d ON s.dataset_id = d.id
        GROUP BY s.source_file
        ORDER BY record_count DESC
    ''').fetchall()

    # Revenue sources
    rev_rows = conn.execute('''
        SELECT source_file, COUNT(*) as record_count
        FROM revenue
        GROUP BY source_file
        ORDER BY record_count DESC
    ''').fetchall()

    conn.close()
    return jsonify({
        'spending': [
            {
                'file':         r[0],
                'dataset_title':r[1],
                'dataset_url':  r[2],
                'records':      r[3],
                'year_from':    r[4],
                'year_to':      r[5],
            }
            for r in rows
        ],
        'revenue': [
            {'file': r[0], 'records': r[1]}
            for r in rev_rows
        ],
    })


# ── Revenue ───────────────────────────────────────────────────────────────────

@app.get('/api/revenue')
def revenue():
    """Return revenue/tax income totals."""
    fy = to_fy(request.args.get('year'))
    conn = get_conn()

    where  = 'WHERE year = ?' if fy else ''
    params = [fy] if fy else []

    rows = conn.execute(f'''
        SELECT category, subcategory, year, SUM(amount_aud) as total
        FROM revenue
        {where}
        GROUP BY category, subcategory, year
        ORDER BY total DESC
    ''', params).fetchall()

    totals = conn.execute(f'''
        SELECT year, SUM(amount_aud) as total
        FROM revenue
        {where}
        GROUP BY year
        ORDER BY year
    ''', params).fetchall()

    conn.close()
    return jsonify({
        'by_category': [
            {'category': r[0], 'subcategory': r[1], 'year': r[2], 'total_aud': r[3]}
            for r in rows
        ],
        'by_year': [
            {'year': r[0], 'total_aud': r[1]}
            for r in totals
        ],
    })


# ── Contracts (AusTender) ─────────────────────────────────────────────────────

@app.get('/api/contracts')
def contracts():
    """
    Return individual contract records.
    Query params: sector, year, agency, search, state, limit, offset
    """
    sector = request.args.get('sector')
    fy     = to_fy(request.args.get('year'))
    agency = request.args.get('agency')
    search = request.args.get('search')
    state  = request.args.get('state')
    limit  = min(int(request.args.get('limit', 50)), 500)
    offset = int(request.args.get('offset', 0))

    where, params = [], []
    if sector: where.append('sector = ?');                      params.append(sector)
    if fy:     where.append('year = ?');                        params.append(fy)
    if agency: where.append('agency LIKE ?');                   params.append(f'%{agency}%')
    if state:  where.append('state = ?');                       params.append(state)
    if search:
        where.append('(description LIKE ? OR supplier LIKE ? OR agency LIKE ?)')
        params += [f'%{search}%', f'%{search}%', f'%{search}%']

    wc = ('WHERE ' + ' AND '.join(where)) if where else ''
    conn = get_conn()

    rows = conn.execute(f'''
        SELECT cn_id, agency, supplier, description, value_aud,
               start_date, end_date, category, sector, state, year
        FROM contracts
        {wc}
        ORDER BY value_aud DESC
        LIMIT ? OFFSET ?
    ''', params + [limit, offset]).fetchall()

    total = conn.execute(f'SELECT COUNT(*) FROM contracts {wc}', params).fetchone()[0]
    conn.close()

    return jsonify({
        'total':   total,
        'limit':   limit,
        'offset':  offset,
        'results': [
            {'cn_id': r[0], 'agency': r[1], 'supplier': r[2], 'description': r[3],
             'value_aud': r[4], 'start_date': r[5], 'end_date': r[6],
             'category': r[7], 'sector': r[8], 'state': r[9], 'year': r[10]}
            for r in rows
        ],
    })


# ── National debt ─────────────────────────────────────────────────────────────

@app.get('/api/debt')
def debt():
    """Return national debt over time, broken down by instrument."""
    conn = get_conn()

    # Latest total per instrument
    by_instrument = conn.execute('''
        SELECT instrument,
               face_value_aud,
               date
        FROM national_debt nd1
        WHERE date = (
            SELECT MAX(date) FROM national_debt nd2
            WHERE nd2.instrument = nd1.instrument
        )
        ORDER BY face_value_aud DESC
    ''').fetchall()

    # Time series of total debt (all instruments summed per date)
    timeseries = conn.execute('''
        SELECT date, SUM(face_value_aud) as total
        FROM national_debt
        GROUP BY date
        ORDER BY date
    ''').fetchall()

    # Record count to show data status
    count = conn.execute('SELECT COUNT(*) FROM national_debt').fetchone()[0]

    conn.close()
    return jsonify({
        'record_count':    count,
        'by_instrument':   [
            {'instrument': r[0], 'face_value_aud': r[1], 'as_at': r[2]}
            for r in by_instrument
        ],
        'timeseries': [
            {'date': r[0], 'total_aud': r[1]}
            for r in timeseries
        ],
    })


# ── HECS/HELP ─────────────────────────────────────────────────────────────────

@app.get('/api/hecs')
def hecs():
    """Return HECS/HELP loan book data."""
    conn = get_conn()

    by_year = conn.execute('''
        SELECT year, category, SUM(amount_aud) as total, SUM(borrower_count) as borrowers
        FROM hecs_debt
        GROUP BY year, category
        ORDER BY year DESC, total DESC
    ''').fetchall()

    # Outstanding debt trend
    outstanding = conn.execute('''
        SELECT year, SUM(amount_aud) as total
        FROM hecs_debt
        WHERE category = 'Total outstanding'
        GROUP BY year
        ORDER BY year
    ''').fetchall()

    count = conn.execute('SELECT COUNT(*) FROM hecs_debt').fetchone()[0]

    conn.close()
    return jsonify({
        'record_count': count,
        'by_year': [
            {'year': r[0], 'category': r[1], 'total_aud': r[2], 'borrowers': r[3]}
            for r in by_year
        ],
        'outstanding_trend': [
            {'year': r[0], 'total_aud': r[1]}
            for r in outstanding
        ],
    })


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # 0.0.0.0 so it's reachable on your local network / Proxmox VM
    app.run(host='0.0.0.0', port=5000, debug=True)
