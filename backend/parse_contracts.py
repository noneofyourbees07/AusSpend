"""
Parse AusTender contract CSV/Excel files into the contracts table.

AusTender column names (standard export format):
  CN ID, Agency, Supplier Name, Description, Value (AUD),
  Contract Start Date, Contract End Date, Category (UNSPSC), Delivery State

Run: python3 parse_contracts.py
"""
import os
import hashlib
import pandas as pd

from db import get_conn, init_db
from parse_spending import classify_sector  # reuse our sector classifier

RAW_DIR = os.path.join(os.path.dirname(__file__), 'data', 'raw')

# AusTender uses fairly consistent column names but with some variation
FIELD_MAP = {
    'cn_id':       ['cn id', 'contract notice id', 'cn_id', 'id'],
    'agency':      ['agency', 'agency name', 'department', 'entity'],
    'supplier':    ['supplier name', 'supplier', 'contractor', 'abn supplier'],
    'description': ['description', 'contract description', 'goods/services description', 'subject matter'],
    'value':       ['value (aud)', 'value', 'contract value', 'amount', 'total value'],
    'start_date':  ['contract start date', 'start date', 'commencement date'],
    'end_date':    ['contract end date', 'end date', 'expiry date'],
    'category':    ['category', 'unspsc', 'procurement category', 'goods/services'],
    'state':       ['delivery state', 'state', 'location', 'delivery location'],
}


def find_col(cols, candidates):
    lower = {c.lower().strip(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    for cand in candidates:
        for k, orig in lower.items():
            if cand.lower() in k or k in cand.lower():
                return orig
    return None


def extract_year(date_str: str) -> str:
    """Extract financial year from a date string like '15/03/2024' or '2024-03-15'."""
    if not date_str:
        return ''
    for sep in ('/', '-'):
        parts = date_str.split(sep)
        for p in parts:
            if len(p) == 4 and p.isdigit():
                yr = int(p)
                # Financial year: July–June
                # A contract starting in e.g. March 2024 is FY 2023-24
                return f'{yr-1}-{str(yr)[2:]}' if int(date_str.split(sep)[1] if sep in date_str else 1) < 7 else f'{yr}-{str(yr+1)[2:]}'
    return ''


def row_hash(*values):
    return hashlib.md5('|'.join(str(v) for v in values).encode()).hexdigest()


def parse_file(path: str) -> list[dict]:
    ext = path.rsplit('.', 1)[-1].lower()
    print(f'  Reading {os.path.basename(path)} ...')
    try:
        if ext == 'csv':
            for enc in ('utf-8', 'latin-1', 'cp1252'):
                try:
                    df = pd.read_csv(path, encoding=enc, dtype=str,
                                     on_bad_lines='skip', low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print('  could not decode file')
                return []
        else:
            df = pd.read_excel(path, dtype=str)
    except Exception as e:
        print(f'  parse error: {e}')
        return []

    df.columns = [str(c).strip() for c in df.columns]
    cols = list(df.columns)

    # Map column names
    mapped = {field: find_col(cols, candidates)
              for field, candidates in FIELD_MAP.items()}

    if not mapped['value'] or not mapped['agency']:
        print(f'  cannot identify required columns.')
        print(f'  columns found: {cols[:8]}')
        return []

    print(f'  {len(df)} rows found, parsing...')
    records = []
    for _, row in df.iterrows():
        def get(field):
            col = mapped.get(field)
            return str(row.get(col, '') or '').strip() if col else ''

        raw_val = get('value').replace('$','').replace(',','').replace(' ','')
        try:
            value = float(raw_val)
        except ValueError:
            continue
        if value <= 0:
            continue

        agency      = get('agency')
        supplier    = get('supplier')
        description = get('description')
        start_date  = get('start_date')
        cn_id       = get('cn_id')
        category    = get('category')
        state       = get('state')
        year        = extract_year(start_date)

        # Classify into our sectors using agency + description + category
        sector = classify_sector(f'{agency} {description} {category}')

        records.append({
            'cn_id':       cn_id,
            'agency':      agency,
            'supplier':    supplier,
            'description': description[:300],
            'value_aud':   value,
            'start_date':  start_date,
            'end_date':    get('end_date'),
            'category':    category[:120],
            'sector':      sector,
            'state':       state,
            'year':        year,
            'source_file': os.path.basename(path),
            'hash':        row_hash(cn_id or agency, supplier, description[:80], value),
        })

    return records


def run():
    init_db()
    conn = get_conn()

    files = [f for f in os.listdir(RAW_DIR)
             if f.startswith('contracts') and f.endswith(('.csv', '.xlsx', '.xls'))]

    if not files:
        print('No contract files found.')
        print('Run fetch_contracts.py first, or manually place AusTender CSVs')
        print('named contracts_YYYY.csv in backend/data/raw/')
        conn.close()
        return

    total = 0
    for filename in sorted(files):
        path = os.path.join(RAW_DIR, filename)
        print(f'\nParsing {filename}')
        records = parse_file(path)
        if not records:
            print('  no records extracted')
            continue

        inserted = 0
        for r in records:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO contracts
                        (cn_id, agency, supplier, description, value_aud,
                         start_date, end_date, category, sector, state, year,
                         source_file, row_hash)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (r['cn_id'], r['agency'], r['supplier'], r['description'],
                      r['value_aud'], r['start_date'], r['end_date'], r['category'],
                      r['sector'], r['state'], r['year'], r['source_file'], r['hash']))
                if conn.execute('SELECT changes()').fetchone()[0]:
                    inserted += 1
            except Exception as e:
                print(f'  insert error: {e}')
        conn.commit()
        total += inserted
        print(f'  ✓ {inserted} contracts loaded')

    conn.close()
    print(f'\n✓ Total: {total} contracts in database.')


if __name__ == '__main__':
    run()
