"""
Polite scraper for AusTender (tenders.gov.au) — fetches recent contract data
that's not on data.gov.au.

How this is polite (and won't get you blocked):
  • Identifies the project clearly in User-Agent
  • Respects robots.txt by checking it first
  • 5 second delay between requests (humans browse slower than that)
  • Caches everything locally — re-runs use cache, never re-fetch
  • Limits to 100 pages per year max (safety)
  • Only fetches the public CSV export endpoint they provide
  • One financial year at a time, with a polite pause between years

What it does NOT do:
  • No headless browsers (Puppeteer/Selenium)
  • No bypassing CAPTCHAs or login walls
  • No parallel requests
  • No HTML parsing of search result pages

This is a citizen using a public dataset for civic transparency.
That's exactly what AusTender is built for.

Run: python3 fetch_austender_search.py
"""
import requests
import os
import time
import urllib.robotparser
from datetime import datetime

from db import init_db

RAW_DIR = os.path.join(os.path.dirname(__file__), 'data', 'raw')

# ── Config ────────────────────────────────────────────────────────────────────

BASE         = 'https://www.tenders.gov.au'
ROBOTS_URL   = f'{BASE}/robots.txt'
SEARCH_URL   = f'{BASE}/Search/CnSearch'
EXPORT_URL   = f'{BASE}/cn/search/dataExport'   # CSV export endpoint
DELAY_SECS   = 5.0     # polite — humans browse slower than this
TIMEOUT_SECS = 30
MAX_RETRIES  = 2

HEADERS = {
    'User-Agent': (
        'AusSpend-Civic-Tool/0.1 '
        '(Open source government spending transparency tool. '
        'Personal/educational use. Contact via GitHub issues.)'
    ),
    'Accept':          'text/csv, application/json, text/html',
    'Accept-Language': 'en-AU,en;q=0.9',
}

# Financial years to attempt — newest first
TARGET_YEARS = [
    ('2024-07-01', '2025-06-30', '2024-25'),
    ('2023-07-01', '2024-06-30', '2023-24'),
    ('2022-07-01', '2023-06-30', '2022-23'),
    ('2021-07-01', '2022-06-30', '2021-22'),
    ('2020-07-01', '2021-06-30', '2020-21'),
    ('2019-07-01', '2020-06-30', '2019-20'),
]


# ── Polite scraping helpers ───────────────────────────────────────────────────

def check_robots():
    """Check robots.txt — bail out if we're not allowed."""
    print(f'Checking {ROBOTS_URL}...')
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(ROBOTS_URL)
    try:
        rp.read()
    except Exception as e:
        print(f'  could not read robots.txt ({e}) — proceeding cautiously')
        return True

    can_fetch = rp.can_fetch(HEADERS['User-Agent'], EXPORT_URL)
    if not can_fetch:
        print(f'  robots.txt DISALLOWS the export endpoint.')
        print(f'  Stopping. We will not fetch from URLs robots.txt forbids.')
        return False
    print(f'  robots.txt allows the export endpoint.')
    return True


def polite_get(url, params=None, attempt=1):
    """GET with polite delays, retries on failure."""
    print(f'  → GET {url}')
    if params:
        print(f'    params: {params}')
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_SECS)
    except requests.RequestException as e:
        if attempt < MAX_RETRIES:
            print(f'    error: {e} — retrying after {DELAY_SECS * 2}s')
            time.sleep(DELAY_SECS * 2)
            return polite_get(url, params, attempt + 1)
        print(f'    error: {e} — giving up')
        return None

    if resp.status_code == 429:
        print(f'    rate limited (429) — backing off 60s')
        time.sleep(60)
        if attempt < MAX_RETRIES:
            return polite_get(url, params, attempt + 1)
        return None

    if resp.status_code >= 400:
        print(f'    HTTP {resp.status_code}')
        return None

    return resp


# ── Fetch one financial year ──────────────────────────────────────────────────

def fetch_year(date_from, date_to, fy_label):
    """Try to download a year's CSV via the export endpoint."""
    dest = os.path.join(RAW_DIR, f'contracts_{fy_label}_austender.csv')
    if os.path.exists(dest) and os.path.getsize(dest) > 1024:
        print(f'  cached: {dest}')
        return True

    print(f'\n── {fy_label} ({date_from} to {date_to}) ──')

    # AusTender export endpoint accepts these params
    params = {
        'PublishDateFrom': date_from,
        'PublishDateTo':   date_to,
    }

    resp = polite_get(EXPORT_URL, params=params)
    if not resp:
        return False

    ctype = resp.headers.get('Content-Type', '')

    # If we got CSV, save it
    if 'csv' in ctype.lower() or resp.content[:5] in (b'CN ID', b'"CN I', b'CNID,'):
        with open(dest, 'wb') as f:
            f.write(resp.content)
        size_kb = len(resp.content) / 1024
        print(f'  ✓ saved {dest} ({size_kb:.0f} KB)')
        return True

    # If we got HTML, the export endpoint isn't accepting our params directly
    if 'html' in ctype.lower():
        print(f'  endpoint returned HTML — export likely needs a session/CSRF token.')
        print(f'  This is normal for some government sites.')
        return False

    print(f'  unexpected content-type: {ctype}')
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    os.makedirs(RAW_DIR, exist_ok=True)
    init_db()

    print('═' * 60)
    print(' AusTender polite fetcher')
    print('═' * 60)
    print()

    if not check_robots():
        return

    print()
    print(f'Will attempt to fetch {len(TARGET_YEARS)} financial years.')
    print(f'Polite delay: {DELAY_SECS}s between requests.')
    print()

    successes = 0
    failures  = 0
    for date_from, date_to, fy_label in TARGET_YEARS:
        ok = fetch_year(date_from, date_to, fy_label)
        if ok:
            successes += 1
        else:
            failures += 1
        time.sleep(DELAY_SECS)

    print()
    print('═' * 60)
    print(f' ✓ {successes} year(s) fetched, {failures} failed')
    print('═' * 60)

    if successes > 0:
        print()
        print('Next: run python3 parse_contracts.py to load into the database.')

    if failures > 0:
        print()
        print('For years that failed, try the manual export:')
        print(f'  1. Visit {SEARCH_URL}')
        print(f'  2. Set "Publish Date" range to the year you want')
        print(f'  3. Click "Search"')
        print(f'  4. Click "Download" → CSV')
        print(f'  5. Save the file in backend/data/raw/')
        print(f'     named contracts_YYYY-YY_austender.csv')
        print(f'  6. Run python3 parse_contracts.py')


if __name__ == '__main__':
    run()
