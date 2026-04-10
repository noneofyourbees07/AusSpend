"""
Fetch budget/spending datasets from data.gov.au using their official CKAN API.
This is NOT scraping — data.gov.au is an open data portal with a public API
designed for exactly this kind of use.

API docs: https://data.gov.au/data/api/3
Rate limits: none stated, but we add polite delays anyway.

Run: python3 fetch_data_gov.py
"""
import requests
import sqlite3
import json
import os
import time
import hashlib

from db import get_conn, init_db, DB_PATH

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL   = 'https://data.gov.au/data/api/3/action'
RAW_DIR    = os.path.join(os.path.dirname(__file__), 'data', 'raw')
DELAY_SECS = 1.5   # polite pause between API calls

# Search terms that tend to return budget/spending datasets
SEARCH_TERMS = [
    'budget expenditure',
    'commonwealth spending',
    'portfolio budget statements',
    'agency financial statements',
    'final budget outcome',
]

HEADERS = {
    # Identify ourselves — good practice, not required
    'User-Agent': 'AusSpend-Research-Tool/0.1 (open source, non-commercial)',
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def search_datasets(query: str, rows: int = 20) -> list[dict]:
    """Query the data.gov.au CKAN API for matching datasets."""
    url    = f'{BASE_URL}/package_search'
    params = {'q': query, 'rows': rows, 'sort': 'score desc'}
    resp   = requests.get(url, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data   = resp.json()
    return data.get('result', {}).get('results', [])


def get_dataset_detail(dataset_id: str) -> dict:
    """Get full metadata + resource list for a dataset."""
    url    = f'{BASE_URL}/package_show'
    params = {'id': dataset_id}
    resp   = requests.get(url, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json().get('result', {})


def download_resource(url: str, filename: str) -> str | None:
    """Download a data file if we don't already have it. Returns local path."""
    dest = os.path.join(RAW_DIR, filename)
    if os.path.exists(dest):
        print(f'  ↳ already have {filename}, skipping download')
        return dest

    print(f'  ↳ downloading {filename} ...')
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        resp.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f'    saved → {dest}')
        return dest
    except Exception as e:
        print(f'    failed: {e}')
        return None


def save_dataset_meta(conn, dataset: dict):
    """Store dataset metadata in the DB."""
    conn.execute('''
        INSERT OR REPLACE INTO datasets (id, title, notes, url, fetched_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    ''', (
        dataset.get('id'),
        dataset.get('title'),
        (dataset.get('notes') or '')[:500],
        f"https://data.gov.au/dataset/{dataset.get('name')}",
    ))
    conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    os.makedirs(RAW_DIR, exist_ok=True)
    init_db()
    conn = get_conn()

    seen_ids = set()

    for term in SEARCH_TERMS:
        print(f'\n── Searching: "{term}" ──')
        try:
            results = search_datasets(term)
        except Exception as e:
            print(f'  API error: {e}')
            time.sleep(DELAY_SECS)
            continue

        print(f'  found {len(results)} datasets')

        for ds in results:
            ds_id = ds.get('id')
            if ds_id in seen_ids:
                continue
            seen_ids.add(ds_id)

            title = ds.get('title', '—')
            print(f'\n  [{ds_id[:8]}] {title}')
            save_dataset_meta(conn, ds)

            # Download CSV/Excel resources from each dataset
            resources = ds.get('resources', [])
            for res in resources:
                fmt    = (res.get('format') or '').upper()
                dl_url = res.get('url') or res.get('download_url')

                if fmt not in ('CSV', 'XLSX', 'XLS') or not dl_url:
                    continue

                # Safe filename: dataset_id + resource_id + extension
                ext      = fmt.lower().replace('xlsx', 'xlsx').replace('xls', 'xls').replace('csv', 'csv')
                filename = f"{ds_id[:8]}_{res['id'][:8]}.{ext}"
                download_resource(dl_url, filename)
                time.sleep(DELAY_SECS)

        time.sleep(DELAY_SECS)

    conn.close()
    print(f'\n✓ Done. Check {RAW_DIR} for downloaded files.')
    print(f'  Run parse_spending.py next to load them into the database.')


if __name__ == '__main__':
    run()
