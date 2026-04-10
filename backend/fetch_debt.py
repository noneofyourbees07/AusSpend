"""
Fetch Australian national debt and HECS/HELP loan data.

Sources:
1. AOFM (Australian Office of Financial Management)
   - Publishes outstanding Commonwealth Government Securities weekly
   - data.gov.au has AOFM datasets
   - aofm.gov.au/statistics also has direct CSV downloads

2. Department of Education — HELP loan book statistics
   - Annual publication of total outstanding HELP debt
   - New loans, repayments, write-offs by year

3. ATO Taxation Statistics — HELP repayments collected via tax system

All official sources, no scraping.

Run: python3 fetch_debt.py
Then: python3 parse_debt.py
"""
import requests
import os
import time

from db import init_db

RAW_DIR    = os.path.join(os.path.dirname(__file__), 'data', 'raw')
DELAY_SECS = 1.5
HEADERS    = {'User-Agent': 'AusSpend-Research-Tool/0.1 (open source, non-commercial)'}
BASE_URL   = 'https://data.gov.au/data/api/3/action'


def search_and_download(query: str, label: str, prefix: str):
    """Search data.gov.au and download matching CSV/Excel files."""
    print(f'\n── {label} ──')
    try:
        resp = requests.get(
            f'{BASE_URL}/package_search',
            params={'q': query, 'rows': 10},
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
        print(f'  • {ds.get("title", "—")}')
        for res in ds.get('resources', []):
            fmt    = (res.get('format') or '').upper()
            dl_url = res.get('url') or res.get('download_url')
            if fmt not in ('CSV', 'XLSX', 'XLS') or not dl_url:
                continue
            filename = f"{prefix}_{ds['id'][:8]}_{res['id'][:8]}.{fmt.lower()}"
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


# AOFM also publishes direct CSV stats — try these known stable URLs
AOFM_DIRECT = [
    {
        'url':      'https://aofm.gov.au/sites/default/files/documents/statistics/domestic_government_securities_outstanding.csv',
        'filename': 'debt_aofm_cgs_outstanding.csv',
        'desc':     'AOFM CGS Outstanding (direct)',
    },
]

def try_aofm_direct():
    """Try to download AOFM statistics directly from their site."""
    print('\n── AOFM direct download ──')
    for item in AOFM_DIRECT:
        dest = os.path.join(RAW_DIR, item['filename'])
        if os.path.exists(dest):
            print(f'  already have {item["filename"]}')
            continue
        print(f'  trying {item["desc"]} ...')
        try:
            r = requests.get(item['url'], headers=HEADERS, timeout=30)
            r.raise_for_status()
            with open(dest, 'wb') as f:
                f.write(r.content)
            print(f'  saved → {dest}')
        except Exception as e:
            print(f'  failed ({e}) — will rely on data.gov.au search instead')
        time.sleep(DELAY_SECS)


SEARCHES = [
    # National debt / CGS
    ('AOFM Commonwealth Government Securities outstanding debt bonds',
     'AOFM — National Debt / CGS', 'debt'),
    ('Australian government debt treasury bonds notes face value',
     'Treasury Bonds & Notes', 'debt'),
    # HECS/HELP
    ('HELP HECS higher education loan program outstanding debt repayment',
     'HELP/HECS Loan Book', 'hecs'),
    ('higher education loan program ATO repayments taxation statistics',
     'HELP Repayments (ATO)', 'hecs'),
    ('department of education HELP debt students loan book statistics',
     'Dept Education HELP Statistics', 'hecs'),
    # Budget — interest payments on debt
    ('commonwealth interest payments debt servicing budget expenditure',
     'Interest/Debt Servicing Costs', 'debt'),
]


def run():
    os.makedirs(RAW_DIR, exist_ok=True)
    init_db()

    try_aofm_direct()

    for query, label, prefix in SEARCHES:
        search_and_download(query, label, prefix)

    print('\n✓ Done.')
    print('  Run: python3 parse_debt.py  to load into the database.')


if __name__ == '__main__':
    run()
