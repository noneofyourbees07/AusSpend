"""
Fetch Australian government revenue / tax income data.

Sources (all official, no scraping):

1. ATO Taxation Statistics — published annually as Excel files
   - Individual income tax, company tax, super fund tax
   - Direct download from ato.gov.au

2. Treasury Final Budget Outcome — published each September after year end
   - Has every revenue line: income tax, GST, excise, customs, etc.
   - Searched via data.gov.au API

Run: python3 fetch_revenue.py
Then: python3 parse_revenue.py
"""
import requests
import os
import time

from db import init_db

RAW_DIR    = os.path.join(os.path.dirname(__file__), 'data', 'raw')
DELAY_SECS = 1.5

HEADERS = {
    'User-Agent': 'AusSpend-Research-Tool/0.1 (open source, non-commercial)',
}

# ── Direct download targets ───────────────────────────────────────────────────
# These are published official files — links are stable year to year.
# We download them directly rather than scraping.

DIRECT_FILES = [
    {
        'url':      'https://data.gov.au/data/dataset/taxation-statistics',
        'search':   True,   # find via API rather than direct URL
        'query':    'taxation statistics ATO',
        'desc':     'ATO Taxation Statistics',
    },
    {
        'url':      'https://data.gov.au/data/dataset/final-budget-outcome',
        'search':   True,
        'query':    'final budget outcome treasury revenue',
        'desc':     'Treasury Final Budget Outcome',
    },
    {
        'url':      'https://data.gov.au/data/dataset/mid-year-economic-fiscal-outlook',
        'search':   True,
        'query':    'MYEFO revenue commonwealth',
        'desc':     'MYEFO Revenue Tables',
    },
]

BASE_URL = 'https://data.gov.au/data/api/3/action'


def search_and_download(query: str, desc: str):
    print(f'\n── {desc} ──')
    url    = f'{BASE_URL}/package_search'
    params = {'q': query, 'rows': 10}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
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

            ext      = fmt.lower()
            filename = f"rev_{ds['id'][:8]}_{res['id'][:8]}.{ext}"
            dest     = os.path.join(RAW_DIR, filename)

            if os.path.exists(dest):
                print(f'    already have {filename}')
                continue

            print(f'    downloading {filename} ...')
            try:
                r = requests.get(dl_url, headers=HEADERS, timeout=60, stream=True)
                r.raise_for_status()
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                print(f'    saved → {dest}')
            except Exception as e:
                print(f'    failed: {e}')
            time.sleep(DELAY_SECS)

        time.sleep(DELAY_SECS)


def run():
    os.makedirs(RAW_DIR, exist_ok=True)
    init_db()

    for target in DIRECT_FILES:
        search_and_download(target['query'], target['desc'])

    print('\n✓ Done. Run parse_revenue.py to load into the database.')


if __name__ == '__main__':
    run()
