"""
Parse downloaded CSV/Excel files from data/raw/ and load spending records
into the SQLite database.

Run after fetch_data_gov.py:
    python3 parse_spending.py

The parser is deliberately tolerant — real government data files have
inconsistent column names, merged cells, header rows at different positions, etc.
We try a few known column name patterns and skip files we can't parse.
"""
import os
import hashlib
import sqlite3
import pandas as pd

from db import get_conn, init_db

RAW_DIR = os.path.join(os.path.dirname(__file__), 'data', 'raw')

# ── Column name candidates ────────────────────────────────────────────────────
# Government CSVs use wildly inconsistent column names.
# These lists are tried in order; first match wins.

ENTITY_COLS   = ['entity', 'agency', 'department', 'organisation', 'portfolio', 'body']
PROGRAM_COLS  = ['program', 'outcome', 'output', 'description', 'program_name', 'activity']
YEAR_COLS     = ['year', 'financial_year', 'fy', 'period', 'budget_year']
AMOUNT_COLS   = ['amount', 'expenditure', 'expense', 'payment', 'actual', 'budget',
                 'total_expenses', 'total_expenditure', 'appropriation', 'value']

# ── Sector keyword classifier ─────────────────────────────────────────────────
# Very simple keyword match — gets replaced by LLM classifier later.
SECTOR_KEYWORDS = {
    'welfare':        ['welfare', 'social', 'centrelink', 'pension', 'jobseeker', 'ndis',
                       'disability', 'family payment', 'housing', 'rent assistance', 'carer'],
    'health':         ['health', 'medicare', 'pharmaceutical', 'hospital', 'mental health',
                       'aged care', 'pbs', 'medical'],
    'defence':        ['defence', 'defense', 'military', 'aukus', 'adf', 'army', 'navy',
                       'air force', 'border force', 'asio', 'asis', 'veteran'],
    'education':      ['education', 'school', 'university', 'tafe', 'vet', 'hecs', 'childcare',
                       'early childhood', 'student'],
    'infrastructure': ['infrastructure', 'transport', 'road', 'rail', 'port', 'airport',
                       'nbn', 'broadband', 'water', 'urban'],
    'environment':    ['environment', 'climate', 'energy', 'renewable', 'emissions', 'nature',
                       'park', 'biodiversity', 'hydrogen', 'solar', 'carbon'],
    'justice':        ['justice', 'legal', 'court', 'afp', 'police', 'attorney', 'nacc',
                       'corruption', 'law reform', 'acic'],
    'economy':        ['treasury', 'tax', 'ato', 'asic', 'apra', 'trade', 'finance',
                       'productivity', 'investment', 'export'],
    'indigenous':     ['indigenous', 'aboriginal', 'torres strait', 'first nations', 'atsic'],
}


def classify_sector(text: str) -> str:
    """Keyword-based sector classification. Returns best match or 'other'."""
    text = text.lower()
    scores = {sector: 0 for sector in SECTOR_KEYWORDS}
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[sector] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'other'


def find_col(df_cols: list[str], candidates: list[str]) -> str | None:
    """Find the first matching column name (case-insensitive)."""
    lower = {c.lower().strip().replace(' ', '_'): c for c in df_cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    # Partial match fallback
    for cand in candidates:
        for col_key, col_orig in lower.items():
            if cand.lower() in col_key:
                return col_orig
    return None


def row_hash(entity, program, year, amount) -> str:
    key = f'{entity}|{program}|{year}|{amount}'
    return hashlib.md5(key.encode()).hexdigest()


def parse_file(path: str) -> list[dict]:
    """Parse a CSV or Excel file into a list of spending records."""
    ext = path.rsplit('.', 1)[-1].lower()
    try:
        if ext == 'csv':
            # Try a few encodings — government CSVs often use latin-1
            for enc in ('utf-8', 'latin-1', 'cp1252'):
                try:
                    df = pd.read_csv(path, encoding=enc, dtype=str, on_bad_lines='skip')
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print(f'  could not decode {os.path.basename(path)}')
                return []
        elif ext in ('xlsx', 'xls'):
            df = pd.read_excel(path, dtype=str)
        else:
            return []
    except Exception as e:
        print(f'  parse error ({os.path.basename(path)}): {e}')
        return []

    # Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    entity_col  = find_col(list(df.columns), ENTITY_COLS)
    program_col = find_col(list(df.columns), PROGRAM_COLS)
    year_col    = find_col(list(df.columns), YEAR_COLS)
    amount_col  = find_col(list(df.columns), AMOUNT_COLS)

    if not (entity_col or program_col) or not amount_col:
        print(f'  could not identify required columns in {os.path.basename(path)}')
        print(f'  columns found: {list(df.columns)[:8]}')
        return []

    records = []
    for _, row in df.iterrows():
        entity  = str(row.get(entity_col,  '') or '').strip() if entity_col  else ''
        program = str(row.get(program_col, '') or '').strip() if program_col else ''
        year    = str(row.get(year_col,    '') or '').strip() if year_col    else ''
        raw_amt = str(row.get(amount_col,  '') or '').strip()

        # Parse amount — strip $, commas, parentheses (negatives)
        raw_amt = raw_amt.replace('$', '').replace(',', '').replace(' ', '')
        negative = raw_amt.startswith('(') or raw_amt.startswith('-')
        raw_amt  = raw_amt.strip('()-')
        try:
            amount = float(raw_amt)
            if negative:
                amount = -amount
        except ValueError:
            continue  # skip rows with no numeric amount

        if amount == 0:
            continue

        combined_text = f'{entity} {program}'
        sector = classify_sector(combined_text)

        records.append({
            'entity':      entity,
            'program':     program,
            'sector':      sector,
            'year':        year,
            'amount_aud':  amount,
            'source_file': os.path.basename(path),
            'hash':        row_hash(entity, program, year, amount),
        })

    return records


def load_records(conn, records: list[dict], dataset_id: str = ''):
    """Insert records into spending table, skipping duplicates."""
    inserted = 0
    for r in records:
        try:
            conn.execute('''
                INSERT OR IGNORE INTO spending
                    (dataset_id, entity, program, sector, year, amount_aud, source_file, row_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dataset_id,
                r['entity'],
                r['program'],
                r['sector'],
                r['year'],
                r['amount_aud'],
                r['source_file'],
                r['hash'],
            ))
            if conn.execute('SELECT changes()').fetchone()[0]:
                inserted += 1
        except Exception as e:
            print(f'  insert error: {e}')
    conn.commit()
    return inserted


def run():
    init_db()
    conn = get_conn()

    files = [f for f in os.listdir(RAW_DIR) if f.endswith(('.csv', '.xlsx', '.xls'))]
    if not files:
        print(f'No files in {RAW_DIR} — run fetch_data_gov.py first.')
        return

    total = 0
    for filename in sorted(files):
        path = os.path.join(RAW_DIR, filename)
        print(f'\nParsing {filename} ...')
        records = parse_file(path)
        if records:
            n = load_records(conn, records)
            total += n
            print(f'  ✓ {n} new records loaded ({len(records)} rows parsed)')
        else:
            print(f'  ✗ no records extracted')

    conn.close()
    print(f'\n✓ Total: {total} spending records in database.')
    print(f'  Run: python3 -c "import db; import sqlite3; ...' )
    print(f'  Or start the Flask API: python3 api.py')


if __name__ == '__main__':
    run()
