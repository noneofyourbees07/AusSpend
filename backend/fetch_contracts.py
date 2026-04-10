"""
Fetch AusTender contract data — individual Commonwealth procurement records.

AusTender is the official source for all Commonwealth contracts >$10,000.
It has a published annual CSV export on data.gov.au — no scraping needed.

Each record shows:
  - Agency name
  - Supplier / contractor
  - Contract description (e.g. "Bruce Highway Upgrade — Cooroy to Curra")
  - Contract value
  - Start/end date
  - UNSPSC category (standardised procurement category)
  - Delivery state

This is what unlocks project-level detail inside each sector —
e.g. infrastructure splits into individual road/rail contracts,
health splits into individual hospital equipment suppliers, etc.

Run: python3 fetch_contracts.py
Then: python3 parse_contracts.py
"""
import requests
import os
import time

from db import init_db

RAW_DIR    = os.path.join(os.path.dirname(__file__), 'data', 'raw')
DELAY_SECS = 1.5
HEADERS    = {'User-Agent': 'AusSpend-Research-Tool/0.1 (open source, non-commercial)'}
BASE_URL   = 'https://data.gov.au/data/api/3/action'

# AusTender publishes annual contract data exports on data.gov.au
# These search terms reliably find them
SEARCHES = [
    ('AusTender contract notice data export annual',
     'AusTender Annual Export', 'contracts'),
    ('Commonwealth procurement contracts awarded expenditure',
     'Commonwealth Contracts', 'contracts'),
    ('austender CN data',
     'AusTender CN Data', 'contracts'),
]


def search_and_download(query: str, label: str, prefix: str):
    print(f'\n── {label} ──')
    try:
        resp = requests.get(
            f'{BASE_URL}/package_search',
            params={'q': query, 'rows': 8},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get('result', {}).get('results', [])
    except Exception as e:
        print(f'  API error: {e}')
        return

    print(f'  found {len(results)} datasets')
    for ds in results:
        title = ds.get('title', '—')
        print(f'  • {title}')
        for res in ds.get('resources', []):
            fmt    = (res.get('format') or '').upper()
            dl_url = res.get('url') or res.get('download_url')
            if fmt not in ('CSV', 'XLSX', 'XLS') or not dl_url:
                continue
            # Skip very large files on first run — AusTender full exports can be >500MB
            # We'll grab by year instead
            res_name = (res.get('name') or res.get('description') or '').lower()
            filename = f"{prefix}_{ds['id'][:8]}_{res['id'][:8]}.{fmt.lower()}"
            dest     = os.path.join(RAW_DIR, filename)
            if os.path.exists(dest):
                print(f'    already have {filename}')
                continue
            print(f'    downloading {filename} ...')
            try:
                # Stream and check size — skip files >100MB
                r = requests.get(dl_url, headers=HEADERS, timeout=10, stream=True)
                r.raise_for_status()
                content_length = int(r.headers.get('content-length', 0))
                if content_length > 100 * 1024 * 1024:
                    print(f'    skipping — file too large ({content_length/1024/1024:.0f}MB). Download manually if needed.')
                    r.close()
                    continue
                with open(dest, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if downloaded > 100 * 1024 * 1024:
                            print(f'    stopping at 100MB — file may be larger')
                            break
                print(f'    saved → {dest}')
            except Exception as e:
                print(f'    failed: {e}')
            time.sleep(DELAY_SECS)
        time.sleep(DELAY_SECS)


def run():
    os.makedirs(RAW_DIR, exist_ok=True)
    init_db()

    for query, label, prefix in SEARCHES:
        search_and_download(query, label, prefix)

    print('\n✓ Done.')
    print('  Run: python3 parse_contracts.py  to load into the database.')
    print()
    print('  Note: AusTender full exports are large. If nothing downloaded,')
    print('  visit https://data.gov.au and search "austender" to find the')
    print('  annual CSV exports and download them manually to data/raw/')
    print('  naming them contracts_YYYY.csv')


if __name__ == '__main__':
    run()
