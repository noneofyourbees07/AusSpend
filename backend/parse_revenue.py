"""
Parse revenue/tax files from data/raw/ (files prefixed rev_) into the revenue table.

Revenue categories we map to:
  - Income Tax — Individuals
  - Income Tax — Companies
  - Income Tax — Superannuation
  - GST
  - Excise & Customs
  - Other Taxes
  - Non-Tax Revenue (fees, dividends, etc.)

Run: python3 parse_revenue.py
"""
import os
import hashlib
import pandas as pd

from db import get_conn, init_db

RAW_DIR = os.path.join(os.path.dirname(__file__), 'data', 'raw')

# Keyword mapping to revenue categories
REVENUE_KEYWORDS = {
    'Income Tax — Individuals':    ['individual', 'personal income', 'paye', 'withholding'],
    'Income Tax — Companies':      ['company', 'corporate', 'companies tax'],
    'Income Tax — Superannuation': ['superannuation', 'super fund', 'super tax'],
    'GST':                         ['gst', 'goods and services tax'],
    'Excise & Customs':            ['excise', 'customs', 'fuel levy', 'tobacco', 'alcohol'],
    'Other Taxes':                 ['fringe benefits', 'fbt', 'stamp duty', 'payroll tax',
                                    'carbon', 'minerals resource', 'petroleum resource'],
    'Non-Tax Revenue':             ['dividend', 'fee', 'charge', 'rent', 'interest',
                                    'non-tax', 'other revenue'],
}

AMOUNT_COLS = ['amount', 'revenue', 'receipts', 'total', 'actual', 'estimate',
               'value', '2023-24', '2022-23', '2021-22', '2020-21']
DESC_COLS   = ['description', 'revenue_type', 'category', 'item', 'head', 'source']
YEAR_COLS   = ['year', 'financial_year', 'fy', 'period']


def classify_revenue(text: str) -> tuple[str, str]:
    """Returns (category, subcategory)."""
    text_lower = text.lower()
    for cat, keywords in REVENUE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return cat, text[:80]
    return 'Other Taxes', text[:80]


def find_col(cols, candidates):
    lower = {c.lower().strip().replace(' ', '_'): c for c in cols}
    for cand in candidates:
        if cand.lower().replace(' ', '_') in lower:
            return lower[cand.lower().replace(' ', '_')]
    for cand in candidates:
        for k, orig in lower.items():
            if cand.lower() in k:
                return orig
    return None


def row_hash(category, subcategory, year, amount):
    key = f'{category}|{subcategory}|{year}|{amount}'
    return hashlib.md5(key.encode()).hexdigest()


def parse_file(path: str) -> list[dict]:
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
        elif ext in ('xlsx', 'xls'):
            df = pd.read_excel(path, dtype=str)
        else:
            return []
    except Exception as e:
        print(f'  parse error: {e}')
        return []

    df.columns = [str(c).strip() for c in df.columns]
    desc_col   = find_col(list(df.columns), DESC_COLS)
    amount_col = find_col(list(df.columns), AMOUNT_COLS)
    year_col   = find_col(list(df.columns), YEAR_COLS)

    if not desc_col or not amount_col:
        print(f'  cannot identify columns. Found: {list(df.columns)[:6]}')
        return []

    records = []
    for _, row in df.iterrows():
        desc   = str(row.get(desc_col,   '') or '').strip()
        year   = str(row.get(year_col,   '') or '').strip() if year_col else ''
        raw    = str(row.get(amount_col, '') or '').strip()

        raw = raw.replace('$', '').replace(',', '').replace(' ', '')
        neg = raw.startswith('(') or raw.startswith('-')
        raw = raw.strip('()-')
        try:
            amount = float(raw)
            if neg:
                amount = -amount
        except ValueError:
            continue

        if amount == 0 or not desc:
            continue

        category, subcat = classify_revenue(desc)
        records.append({
            'category':    category,
            'subcategory': subcat,
            'year':        year,
            'amount_aud':  amount,
            'source_file': os.path.basename(path),
            'hash':        row_hash(category, subcat, year, amount),
        })

    return records


def run():
    init_db()
    conn = get_conn()

    # Only process files prefixed with rev_
    files = [f for f in os.listdir(RAW_DIR)
             if f.startswith('rev_') and f.endswith(('.csv', '.xlsx', '.xls'))]

    if not files:
        print('No revenue files found (expected files starting with rev_)')
        print('Run fetch_revenue.py first.')
        return

    total = 0
    for filename in sorted(files):
        path = os.path.join(RAW_DIR, filename)
        print(f'\nParsing {filename} ...')
        records = parse_file(path)
        if not records:
            print('  no records extracted')
            continue

        inserted = 0
        for r in records:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO revenue
                        (category, subcategory, year, amount_aud, source_file, row_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (r['category'], r['subcategory'], r['year'],
                      r['amount_aud'], r['source_file'], r['hash']))
                if conn.execute('SELECT changes()').fetchone()[0]:
                    inserted += 1
            except Exception as e:
                print(f'  insert error: {e}')
        conn.commit()
        total += inserted
        print(f'  ✓ {inserted} new revenue records')

    conn.close()
    print(f'\n✓ Total: {total} revenue records loaded.')


if __name__ == '__main__':
    run()
