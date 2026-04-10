"""
Fetch recent contract data directly from the AusTender API.

The data.gov.au exports only had up to 2019. But AusTender itself
(tenders.gov.au) has a public search API with all contracts up to today.

This is NOT scraping — AusTender provides these endpoints specifically
for programmatic access. We use their published CN (Contract Notice)
search endpoint.

API: https://www.tenders.gov.au/Search/CnAdvancedSearch
Docs: (limited, but well-known public endpoint)

We fetch in batches by financial year to keep requests reasonable.
Rate-limited with 2 second delays between pages.

Run: python3 fetch_austender_api.py
"""
import requests
import hashlib
import time
import os

from db import get_conn, init_db
from parse_spending import classify_sector

DELAY_SECS = 2.0
HEADERS = {
    'User-Agent': 'AusSpend-Research-Tool/0.1 (open source, non-commercial)',
    'Accept': 'application/json',
}

# AusTender advanced search endpoint
BASE_URL = 'https://www.tenders.gov.au/Search/CnAdvancedSearchResult'

# Financial years to fetch (the ones we're missing)
YEARS_TO_FETCH = [
    ('2019-07-01', '2020-06-30', '2019-20'),
    ('2020-07-01', '2021-06-30', '2020-21'),
    ('2021-07-01', '2022-06-30', '2021-22'),
    ('2022-07-01', '2023-06-30', '2022-23'),
    ('2023-07-01', '2024-06-30', '2023-24'),
    ('2024-07-01', '2025-06-30', '2024-25'),
]


def row_hash(*values):
    return hashlib.md5('|'.join(str(v) for v in values).encode()).hexdigest()


def parse_date_to_fy(date_str):
    """Convert date string to financial year."""
    if not date_str:
        return ''
    # Try common formats
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str[:10], fmt)
            yr = dt.year
            if dt.month >= 7:
                return f'{yr}-{str(yr+1)[2:]}'
            else:
                return f'{yr-1}-{str(yr)[2:]}'
        except ValueError:
            continue
    return ''


def fetch_year(start_date, end_date, fy_label, conn):
    """Fetch all contract notices for a financial year via AusTender search."""
    print(f'\n── Fetching {fy_label} ({start_date} to {end_date}) ──')

    page = 0
    total_inserted = 0
    max_pages = 50  # safety limit — each page is ~20 results

    while page < max_pages:
        params = {
            'SearchFrom': start_date,
            'SearchTo': end_date,
            'Type': 'cn',     # Contract Notices
            'AgencyStatus': 0,
            'Page': page,
        }

        try:
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)

            # If we get HTML (not JSON), the API doesn't support JSON responses
            # In that case we need to parse the HTML or use a different approach
            if 'application/json' not in resp.headers.get('Content-Type', ''):
                if page == 0:
                    print(f'  AusTender returned HTML, not JSON.')
                    print(f'  The direct API may require different parameters.')
                    print(f'  Trying alternative approach...')
                    return fetch_year_alt(start_date, end_date, fy_label, conn)
                break

            resp.raise_for_status()
            data = resp.json()

        except Exception as e:
            print(f'  Error on page {page}: {e}')
            break

        results = data if isinstance(data, list) else data.get('results', data.get('data', []))
        if not results:
            break

        inserted = 0
        for item in results:
            cn_id       = str(item.get('CNID', item.get('cn_id', ''))).strip()
            agency      = str(item.get('Agency', item.get('agency', ''))).strip()
            supplier    = str(item.get('Supplier', item.get('supplier_name', ''))).strip()
            description = str(item.get('Description', item.get('description', ''))).strip()[:300]
            value_str   = str(item.get('Value', item.get('contract_value', '0'))).strip()
            start       = str(item.get('StartDate', item.get('contract_start', ''))).strip()
            end         = str(item.get('EndDate', item.get('contract_end', ''))).strip()
            category    = str(item.get('Category', item.get('unspsc', ''))).strip()[:120]
            state       = str(item.get('State', item.get('delivery_state', ''))).strip().upper()

            # Parse value
            value_str = value_str.replace('$', '').replace(',', '').replace(' ', '')
            try:
                value = float(value_str)
            except ValueError:
                continue
            if value <= 0:
                continue

            sector = classify_sector(f'{agency} {description} {category}')
            h = row_hash(cn_id or agency, supplier, description[:80], value)

            try:
                conn.execute('''
                    INSERT OR IGNORE INTO contracts
                        (cn_id, agency, supplier, description, value_aud,
                         start_date, end_date, category, sector, state, year,
                         source_file, row_hash)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (cn_id, agency, supplier, description, value,
                      start, end, category, sector, state, fy_label,
                      f'austender_api_{fy_label}', h))
                if conn.execute('SELECT changes()').fetchone()[0]:
                    inserted += 1
            except Exception as e:
                pass

        conn.commit()
        total_inserted += inserted
        print(f'  page {page}: {inserted} new contracts')

        if len(results) < 15:  # last page
            break

        page += 1
        time.sleep(DELAY_SECS)

    print(f'  Total for {fy_label}: {total_inserted} contracts')
    return total_inserted


def fetch_year_alt(start_date, end_date, fy_label, conn):
    """Alternative: try the data.gov.au CKAN API for recent AusTender data."""
    print(f'  Trying data.gov.au for recent AusTender data...')

    search_url = 'https://data.gov.au/data/api/3/action/package_search'
    try:
        resp = requests.get(search_url, params={
            'q': f'austender contract notice {fy_label}',
            'rows': 5,
        }, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        results = resp.json().get('result', {}).get('results', [])

        for ds in results:
            title = ds.get('title', '')
            print(f'  Found: {title}')
            for res in ds.get('resources', []):
                fmt = (res.get('format') or '').upper()
                if fmt in ('CSV', 'XLSX'):
                    url = res.get('url') or res.get('download_url')
                    if url:
                        filename = f"contracts_api_{ds['id'][:8]}_{res['id'][:8]}.{fmt.lower()}"
                        dest = os.path.join(os.path.dirname(__file__), 'data', 'raw', filename)
                        if os.path.exists(dest):
                            print(f'    already have {filename}')
                            continue
                        print(f'    downloading {filename}...')
                        try:
                            r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
                            r.raise_for_status()
                            size = int(r.headers.get('content-length', 0))
                            if size > 200 * 1024 * 1024:
                                print(f'    too large ({size/1024/1024:.0f}MB), skipping')
                                continue
                            with open(dest, 'wb') as f:
                                for chunk in r.iter_content(8192):
                                    f.write(chunk)
                            print(f'    saved → {filename}')
                            print(f'    Run parse_contracts.py to load it')
                        except Exception as e:
                            print(f'    failed: {e}')
                        time.sleep(DELAY_SECS)

    except Exception as e:
        print(f'  data.gov.au search failed: {e}')

    return 0


def run():
    init_db()
    conn = get_conn()

    total = 0
    for start, end, label in YEARS_TO_FETCH:
        # Check if we already have data for this year
        existing = conn.execute(
            'SELECT COUNT(*) FROM contracts WHERE year = ?', (label,)
        ).fetchone()[0]
        if existing > 100:
            print(f'\n── {label}: already have {existing} contracts, skipping ──')
            continue
        total += fetch_year(start, end, label, conn)

    conn.close()
    print(f'\n✓ Done. {total} new contracts fetched.')
    if total == 0:
        print()
        print('  If the API returned HTML instead of JSON, you may need to')
        print('  download AusTender data manually:')
        print('  1. Go to https://www.tenders.gov.au/Search/CnSearch')
        print('  2. Filter by date range and export as CSV')
        print('  3. Save as contracts_YYYY-YY.csv in backend/data/raw/')
        print('  4. Run: python3 parse_contracts.py')


if __name__ == '__main__':
    run()
