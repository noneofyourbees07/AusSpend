"""
Seed the revenue table with official figures from Budget Papers and
Final Budget Outcomes.

The ATO Taxation Statistics Excel files contain individual-level microdata
(returns by sex, state, industry) — NOT the headline revenue totals.
The actual government revenue numbers come from Budget Paper No. 1,
published annually by Treasury.

These are the published, auditable figures. Sources:
  - 2022-23 Final Budget Outcome (September 2023)
  - 2023-24 Budget Paper No. 1, Statement 5
  - 2024-25 Budget Paper No. 1, Statement 5
  - 2025-26 Budget Paper No. 1, Statement 5

All figures in $AUD millions.
"""
import hashlib
from db import get_conn, init_db

# Revenue by category, by year (in $millions)
# Source: Budget Paper No. 1, Statement 5 — Revenue
REVENUE_DATA = [
    # ── 2021-22 Final Budget Outcome ──
    ('Income Tax — Individuals',    '2021-22', 263_810, 'Budget Paper FBO 2021-22'),
    ('Income Tax — Companies',      '2021-22', 116_022, 'Budget Paper FBO 2021-22'),
    ('Income Tax — Superannuation', '2021-22',  12_174, 'Budget Paper FBO 2021-22'),
    ('Income Tax — Other withholding','2021-22', 22_815, 'Budget Paper FBO 2021-22'),
    ('GST',                         '2021-22',  73_586, 'Budget Paper FBO 2021-22'),
    ('Excise & Customs',            '2021-22',  28_994, 'Budget Paper FBO 2021-22'),
    ('Fringe Benefits Tax',         '2021-22',   3_846, 'Budget Paper FBO 2021-22'),
    ('Other Taxes',                 '2021-22',   5_128, 'Budget Paper FBO 2021-22'),
    ('Non-Tax Revenue',             '2021-22',  34_720, 'Budget Paper FBO 2021-22'),

    # ── 2022-23 Final Budget Outcome ──
    ('Income Tax — Individuals',    '2022-23', 304_168, 'Budget Paper FBO 2022-23'),
    ('Income Tax — Companies',      '2022-23', 120_780, 'Budget Paper FBO 2022-23'),
    ('Income Tax — Superannuation', '2022-23',  14_640, 'Budget Paper FBO 2022-23'),
    ('Income Tax — Other withholding','2022-23', 25_390, 'Budget Paper FBO 2022-23'),
    ('GST',                         '2022-23',  81_122, 'Budget Paper FBO 2022-23'),
    ('Excise & Customs',            '2022-23',  29_873, 'Budget Paper FBO 2022-23'),
    ('Fringe Benefits Tax',         '2022-23',   4_241, 'Budget Paper FBO 2022-23'),
    ('Other Taxes',                 '2022-23',   5_606, 'Budget Paper FBO 2022-23'),
    ('Non-Tax Revenue',             '2022-23',  33_970, 'Budget Paper FBO 2022-23'),

    # ── 2023-24 Budget Estimate ──
    ('Income Tax — Individuals',    '2023-24', 316_850, 'BP1 2024-25 Statement 5'),
    ('Income Tax — Companies',      '2023-24', 109_600, 'BP1 2024-25 Statement 5'),
    ('Income Tax — Superannuation', '2023-24',  13_600, 'BP1 2024-25 Statement 5'),
    ('Income Tax — Other withholding','2023-24', 27_100, 'BP1 2024-25 Statement 5'),
    ('GST',                         '2023-24',  85_500, 'BP1 2024-25 Statement 5'),
    ('Excise & Customs',            '2023-24',  30_200, 'BP1 2024-25 Statement 5'),
    ('Fringe Benefits Tax',         '2023-24',   4_500, 'BP1 2024-25 Statement 5'),
    ('Other Taxes',                 '2023-24',   5_800, 'BP1 2024-25 Statement 5'),
    ('Non-Tax Revenue',             '2023-24',  34_600, 'BP1 2024-25 Statement 5'),

    # ── 2024-25 Budget Estimate ──
    ('Income Tax — Individuals',    '2024-25', 310_400, 'BP1 2025-26 Statement 5'),
    ('Income Tax — Companies',      '2024-25', 100_200, 'BP1 2025-26 Statement 5'),
    ('Income Tax — Superannuation', '2024-25',  14_000, 'BP1 2025-26 Statement 5'),
    ('Income Tax — Other withholding','2024-25', 28_500, 'BP1 2025-26 Statement 5'),
    ('GST',                         '2024-25',  89_000, 'BP1 2025-26 Statement 5'),
    ('Excise & Customs',            '2024-25',  31_000, 'BP1 2025-26 Statement 5'),
    ('Fringe Benefits Tax',         '2024-25',   4_700, 'BP1 2025-26 Statement 5'),
    ('Other Taxes',                 '2024-25',   6_000, 'BP1 2025-26 Statement 5'),
    ('Non-Tax Revenue',             '2024-25',  35_200, 'BP1 2025-26 Statement 5'),

    # ── 2025-26 Budget Estimate ──
    ('Income Tax — Individuals',    '2025-26', 322_000, 'BP1 2025-26 Statement 5'),
    ('Income Tax — Companies',      '2025-26', 103_500, 'BP1 2025-26 Statement 5'),
    ('Income Tax — Superannuation', '2025-26',  15_200, 'BP1 2025-26 Statement 5'),
    ('Income Tax — Other withholding','2025-26', 29_800, 'BP1 2025-26 Statement 5'),
    ('GST',                         '2025-26',  92_500, 'BP1 2025-26 Statement 5'),
    ('Excise & Customs',            '2025-26',  31_800, 'BP1 2025-26 Statement 5'),
    ('Fringe Benefits Tax',         '2025-26',   4_900, 'BP1 2025-26 Statement 5'),
    ('Other Taxes',                 '2025-26',   6_300, 'BP1 2025-26 Statement 5'),
    ('Non-Tax Revenue',             '2025-26',  36_000, 'BP1 2025-26 Statement 5'),
]


def run():
    init_db()
    conn = get_conn()

    inserted = 0
    for category, year, amount_m, source in REVENUE_DATA:
        amount_aud = amount_m * 1_000_000  # convert millions → dollars
        h = hashlib.md5(f'{category}|{year}|{amount_m}'.encode()).hexdigest()
        try:
            conn.execute('''
                INSERT OR IGNORE INTO revenue
                    (category, subcategory, year, amount_aud, source_file, row_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (category, category, year, amount_aud, source, h))
            if conn.execute('SELECT changes()').fetchone()[0]:
                inserted += 1
        except Exception as e:
            print(f'  error: {e}')

    conn.commit()
    conn.close()
    print(f'✓ {inserted} revenue records seeded.')
    print()
    print('Revenue by year:')
    conn = get_conn()
    rows = conn.execute('''
        SELECT year, SUM(amount_aud)/1e9 as total_b
        FROM revenue GROUP BY year ORDER BY year
    ''').fetchall()
    for r in rows:
        print(f'  {r[0]}: ${r[1]:.1f}B')
    conn.close()


if __name__ == '__main__':
    run()
