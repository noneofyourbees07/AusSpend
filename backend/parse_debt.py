"""
Parse national debt (AOFM) and HECS/HELP files into the database.

Files prefixed debt_ → national_debt table
Files prefixed hecs_ → hecs_debt table

Run: python3 parse_debt.py
"""
import os
import hashlib
import pandas as pd
import re

from db import get_conn, init_db

RAW_DIR = os.path.join(os.path.dirname(__file__), 'data', 'raw')


# ── AOFM / National debt parsing ─────────────────────────────────────────────

INSTRUMENT_KEYWORDS = {
    'Treasury Bond':    ['treasury bond', 't-bond', 'tsy bond', 'acgb'],
    'Treasury Note':    ['treasury note', 't-note', 'tsy note'],
    'Indexed Bond':     ['indexed', 'cib', 'inflation'],
    'Total CGS':        ['total', 'aggregate', 'gross'],
}

DATE_COLS       = ['date', 'period', 'as_at', 'as at', 'month', 'quarter']
AMOUNT_COLS     = ['face_value', 'outstanding', 'amount', 'value', 'total', 'balance']
INSTRUMENT_COLS = ['instrument', 'security', 'type', 'description', 'category']


def classify_instrument(text: str) -> str:
    t = text.lower()
    for name, keywords in INSTRUMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return name
    return text[:60]


def find_col(cols, candidates):
    lower = {c.lower().strip().replace(' ', '_'): c for c in cols}
    for cand in candidates:
        key = cand.lower().replace(' ', '_')
        if key in lower:
            return lower[key]
    for cand in candidates:
        for k, orig in lower.items():
            if cand.lower().replace(' ', '_') in k:
                return orig
    return None


def parse_debt_file(path: str) -> list[dict]:
    ext = path.rsplit('.', 1)[-1].lower()
    try:
        if ext == 'csv':
            for enc in ('utf-8', 'latin-1', 'cp1252'):
                try:
                    df = pd.read_csv(path, encoding=enc, dtype=str, on_bad_lines='skip')
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return []
        else:
            df = pd.read_excel(path, dtype=str)
    except Exception as e:
        print(f'  parse error: {e}')
        return []

    df.columns = [str(c).strip() for c in df.columns]
    date_col   = find_col(list(df.columns), DATE_COLS)
    amount_col = find_col(list(df.columns), AMOUNT_COLS)
    instr_col  = find_col(list(df.columns), INSTRUMENT_COLS)

    if not amount_col:
        print(f'  no amount column found. Columns: {list(df.columns)[:6]}')
        return []

    records = []
    for _, row in df.iterrows():
        date   = str(row.get(date_col,  '') or '').strip() if date_col  else ''
        instr  = str(row.get(instr_col, '') or '').strip() if instr_col else 'Total CGS'
        raw    = str(row.get(amount_col,'') or '').strip()

        raw = raw.replace('$','').replace(',','').replace(' ','')
        try:
            amount = float(raw)
        except ValueError:
            continue
        if amount == 0:
            continue

        instrument = classify_instrument(instr) if instr else 'Total CGS'
        h = hashlib.md5(f'{date}|{instrument}|{amount}'.encode()).hexdigest()
        records.append({
            'date':           date,
            'instrument':     instrument,
            'face_value_aud': amount,
            'source_file':    os.path.basename(path),
            'hash':           h,
        })
    return records


# ── HECS/HELP parsing ─────────────────────────────────────────────────────────

HECS_CATEGORY_KEYWORDS = {
    'Total outstanding':   ['outstanding', 'total debt', 'loan book', 'balance'],
    'New loans issued':    ['new loan', 'new debt', 'issued', 'originated', 'disbursed'],
    'Repayments collected':['repayment', 'collected', 'compulsory repayment', 'voluntary'],
    'Write-offs':          ['write-off', 'write off', 'bad debt', 'impaired'],
    'Indexation':          ['indexation', 'cpi adjustment', 'indexed'],
}


def classify_hecs(text: str) -> str:
    t = text.lower()
    for cat, keywords in HECS_CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return cat
    return 'Other'


def parse_hecs_file(path: str) -> list[dict]:
    ext = path.rsplit('.', 1)[-1].lower()
    try:
        if ext == 'csv':
            for enc in ('utf-8', 'latin-1'):
                try:
                    df = pd.read_csv(path, encoding=enc, dtype=str, on_bad_lines='skip')
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return []
        else:
            df = pd.read_excel(path, dtype=str)
    except Exception as e:
        print(f'  parse error: {e}')
        return []

    df.columns = [str(c).strip() for c in df.columns]
    desc_col   = find_col(list(df.columns), ['description', 'category', 'item', 'loan_type', 'type'])
    year_col   = find_col(list(df.columns), ['year', 'financial_year', 'fy', 'period'])
    amount_col = find_col(list(df.columns), ['amount', 'value', 'total', 'debt', 'balance', 'repayment'])
    count_col  = find_col(list(df.columns), ['borrowers', 'debtors', 'count', 'number', 'students'])

    if not amount_col:
        print(f'  no amount column. Columns: {list(df.columns)[:6]}')
        return []

    records = []
    for _, row in df.iterrows():
        desc   = str(row.get(desc_col,   '') or '').strip() if desc_col   else ''
        year   = str(row.get(year_col,   '') or '').strip() if year_col   else ''
        raw    = str(row.get(amount_col, '') or '').strip()
        count_raw = str(row.get(count_col, '') or '').strip() if count_col else ''

        raw = raw.replace('$','').replace(',','').replace(' ','')
        try:
            amount = float(raw)
        except ValueError:
            continue
        if amount == 0:
            continue

        try:
            count = int(float(count_raw.replace(',',''))) if count_raw else None
        except ValueError:
            count = None

        category = classify_hecs(desc) if desc else 'Other'
        h = hashlib.md5(f'{year}|{category}|{desc}|{amount}'.encode()).hexdigest()
        records.append({
            'year':         year,
            'category':     category,
            'amount_aud':   amount,
            'borrower_count': count,
            'source_file':  os.path.basename(path),
            'hash':         h,
        })
    return records


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    init_db()
    conn = get_conn()

    debt_files = [f for f in os.listdir(RAW_DIR)
                  if f.startswith('debt_') and f.endswith(('.csv','.xlsx','.xls'))]
    hecs_files = [f for f in os.listdir(RAW_DIR)
                  if f.startswith('hecs_') and f.endswith(('.csv','.xlsx','.xls'))]

    if not debt_files and not hecs_files:
        print('No debt/hecs files found. Run fetch_debt.py first.')
        conn.close()
        return

    total_debt = 0
    for f in sorted(debt_files):
        path = os.path.join(RAW_DIR, f)
        print(f'\nParsing debt file: {f}')
        records = parse_debt_file(path)
        inserted = 0
        for r in records:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO national_debt
                        (date, instrument, face_value_aud, source_file, row_hash)
                    VALUES (?, ?, ?, ?, ?)
                ''', (r['date'], r['instrument'], r['face_value_aud'], r['source_file'], r['hash']))
                if conn.execute('SELECT changes()').fetchone()[0]:
                    inserted += 1
            except Exception as e:
                print(f'  insert error: {e}')
        conn.commit()
        total_debt += inserted
        print(f'  ✓ {inserted} debt records')

    total_hecs = 0
    for f in sorted(hecs_files):
        path = os.path.join(RAW_DIR, f)
        print(f'\nParsing HECS file: {f}')
        records = parse_hecs_file(path)
        inserted = 0
        for r in records:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO hecs_debt
                        (year, category, amount_aud, borrower_count, source_file, row_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (r['year'], r['category'], r['amount_aud'],
                      r['borrower_count'], r['source_file'], r['hash']))
                if conn.execute('SELECT changes()').fetchone()[0]:
                    inserted += 1
            except Exception as e:
                print(f'  insert error: {e}')
        conn.commit()
        total_hecs += inserted
        print(f'  ✓ {inserted} HECS records')

    conn.close()
    print(f'\n✓ {total_debt} national debt records, {total_hecs} HECS records loaded.')


if __name__ == '__main__':
    run()
