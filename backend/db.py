"""
Database setup — creates the SQLite schema.
Run once: python3 db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'ausspend.db')


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Raw datasets pulled from data.gov.au
    c.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id          TEXT PRIMARY KEY,
            title       TEXT,
            notes       TEXT,
            url         TEXT,
            fetched_at  TEXT
        )
    ''')

    # Individual spending line items
    c.execute('''
        CREATE TABLE IF NOT EXISTS spending (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id      TEXT,
            entity          TEXT,   -- department / agency name
            program         TEXT,   -- program or output name
            sector          TEXT,   -- our classification (welfare, health, etc.)
            year            TEXT,   -- e.g. "2023-24"
            amount_aud      REAL,   -- dollars
            source_file     TEXT,
            row_hash        TEXT UNIQUE  -- dedup key
        )
    ''')

    # AusTender contracts — individual procurement records
    c.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            cn_id               TEXT,       -- AusTender contract notice ID
            agency              TEXT,
            supplier            TEXT,
            description         TEXT,
            value_aud           REAL,
            start_date          TEXT,
            end_date            TEXT,
            category            TEXT,       -- UNSPSC category description
            sector              TEXT,       -- our classification
            state               TEXT,       -- delivery state
            year                TEXT,
            source_file         TEXT,
            row_hash            TEXT UNIQUE
        )
    ''')

    # News / context items linked to a sector
    c.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sector      TEXT,
            headline    TEXT,
            source      TEXT,
            url         TEXT,
            published   TEXT,
            fetched_at  TEXT
        )
    ''')

    # Revenue / tax income lines (ATO + Treasury Final Budget Outcome)
    c.execute('''
        CREATE TABLE IF NOT EXISTS revenue (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            category        TEXT,   -- e.g. "Income Tax - Individuals"
            subcategory     TEXT,
            year            TEXT,
            amount_aud      REAL,
            source_file     TEXT,
            row_hash        TEXT UNIQUE
        )
    ''')

    # National debt — AOFM Commonwealth Government Securities
    c.execute('''
        CREATE TABLE IF NOT EXISTS national_debt (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT,   -- e.g. "2024-09-30"
            instrument      TEXT,   -- "Treasury Bond", "Treasury Note", "Total"
            face_value_aud  REAL,   -- dollars
            source_file     TEXT,
            row_hash        TEXT UNIQUE
        )
    ''')

    # HECS/HELP student loan book
    c.execute('''
        CREATE TABLE IF NOT EXISTS hecs_debt (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            year            TEXT,
            category        TEXT,   -- "New loans issued", "Repayments collected", "Total outstanding", "Write-offs"
            amount_aud      REAL,
            borrower_count  INTEGER,
            source_file     TEXT,
            row_hash        TEXT UNIQUE
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialised at {DB_PATH}")


if __name__ == '__main__':
    init_db()
