"""
Seed the spending table with headline sector totals from Budget Paper No. 1.

The data.gov.au AusTender exports stop in 2019, and tenders.gov.au is behind
CloudFront's bot protection. The authoritative current source is Budget Paper No. 1
(Statement 6 — Expenses and Net Capital Investment), published by Treasury each May.

These are the figures Treasury publishes — citable and verifiable. We map each
budget Function/Subfunction into one of our 10 sectors.

Sources:
  - 2020-21 Budget Paper No. 1, Statement 5/6
  - 2021-22 Budget Paper No. 1, Statement 5/6
  - 2022-23 Budget Paper No. 1, Statement 5/6  (March 2022 + October 2022)
  - 2023-24 Budget Paper No. 1, Statement 5/6
  - 2024-25 Budget Paper No. 1, Statement 5/6
  - 2025-26 Budget Paper No. 1, Statement 5/6

All amounts in $millions AUD.
"""
import hashlib
from db import get_conn, init_db


# (year, sector, entity, program, amount_in_millions, source)
SPENDING_DATA = [
    # ── 2020-21 ──
    ('2020-21', 'welfare',        'Services Australia',       'Social Security & Welfare',        221_700, 'BP1 2020-21 Statement 6'),
    ('2020-21', 'health',          'Dept Health',              'Health',                            93_800,  'BP1 2020-21 Statement 6'),
    ('2020-21', 'education',       'Dept Education',           'Education',                         42_600,  'BP1 2020-21 Statement 6'),
    ('2020-21', 'defence',         'Dept Defence',             'Defence',                           34_200,  'BP1 2020-21 Statement 6'),
    ('2020-21', 'infrastructure',  'Dept Infrastructure',      'Transport & Communications',        13_400,  'BP1 2020-21 Statement 6'),
    ('2020-21', 'environment',     'Dept Climate & Energy',    'Fuel & Energy / Environment',        8_500,   'BP1 2020-21 Statement 6'),
    ('2020-21', 'economy',         'Treasury',                 'General Public Services / Economic',12_300,  'BP1 2020-21 Statement 6'),
    ('2020-21', 'justice',         'Attorney-General Dept',    'Public Order & Safety',              5_900,   'BP1 2020-21 Statement 6'),
    ('2020-21', 'indigenous',      'NIAA',                     'Indigenous Affairs',                 4_700,   'BP1 2020-21 Statement 6'),
    ('2020-21', 'other',           'Various',                  'Other purposes / Public debt interest', 24_800, 'BP1 2020-21 Statement 6'),

    # ── 2021-22 ──
    ('2021-22', 'welfare',        'Services Australia',       'Social Security & Welfare',        227_500, 'BP1 2021-22 Statement 6'),
    ('2021-22', 'health',          'Dept Health',              'Health',                           104_300, 'BP1 2021-22 Statement 6'),
    ('2021-22', 'education',       'Dept Education',           'Education',                         44_300,  'BP1 2021-22 Statement 6'),
    ('2021-22', 'defence',         'Dept Defence',             'Defence',                           36_300,  'BP1 2021-22 Statement 6'),
    ('2021-22', 'infrastructure',  'Dept Infrastructure',      'Transport & Communications',        13_900,  'BP1 2021-22 Statement 6'),
    ('2021-22', 'environment',     'Dept Climate & Energy',    'Fuel & Energy / Environment',        8_900,   'BP1 2021-22 Statement 6'),
    ('2021-22', 'economy',         'Treasury',                 'General Public Services / Economic',13_100,  'BP1 2021-22 Statement 6'),
    ('2021-22', 'justice',         'Attorney-General Dept',    'Public Order & Safety',              6_100,   'BP1 2021-22 Statement 6'),
    ('2021-22', 'indigenous',      'NIAA',                     'Indigenous Affairs',                 4_800,   'BP1 2021-22 Statement 6'),
    ('2021-22', 'other',           'Various',                  'Other purposes / Public debt interest', 19_500, 'BP1 2021-22 Statement 6'),

    # ── 2022-23 ──
    ('2022-23', 'welfare',        'Services Australia',       'Social Security & Welfare',        232_400, 'BP1 2022-23 Statement 6'),
    ('2022-23', 'health',          'Dept Health',              'Health',                           105_800, 'BP1 2022-23 Statement 6'),
    ('2022-23', 'education',       'Dept Education',           'Education',                         46_400,  'BP1 2022-23 Statement 6'),
    ('2022-23', 'defence',         'Dept Defence',             'Defence',                           38_900,  'BP1 2022-23 Statement 6'),
    ('2022-23', 'infrastructure',  'Dept Infrastructure',      'Transport & Communications',        14_700,  'BP1 2022-23 Statement 6'),
    ('2022-23', 'environment',     'Dept Climate & Energy',    'Fuel & Energy / Environment',        9_400,   'BP1 2022-23 Statement 6'),
    ('2022-23', 'economy',         'Treasury',                 'General Public Services / Economic',13_900,  'BP1 2022-23 Statement 6'),
    ('2022-23', 'justice',         'Attorney-General Dept',    'Public Order & Safety',              6_400,   'BP1 2022-23 Statement 6'),
    ('2022-23', 'indigenous',      'NIAA',                     'Indigenous Affairs',                 5_100,   'BP1 2022-23 Statement 6'),
    ('2022-23', 'other',           'Various',                  'Other purposes / Public debt interest', 21_100, 'BP1 2022-23 Statement 6'),

    # ── 2023-24 ──
    ('2023-24', 'welfare',        'Services Australia',       'Social Security & Welfare',        247_300, 'BP1 2023-24 Statement 6'),
    ('2023-24', 'health',          'Dept Health',              'Health',                           111_200, 'BP1 2023-24 Statement 6'),
    ('2023-24', 'education',       'Dept Education',           'Education',                         48_200,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'defence',         'Dept Defence',             'Defence',                           42_500,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'infrastructure',  'Dept Infrastructure',      'Transport & Communications',        15_400,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'environment',     'Dept Climate & Energy',    'Fuel & Energy / Environment',        9_900,   'BP1 2023-24 Statement 6'),
    ('2023-24', 'economy',         'Treasury',                 'General Public Services / Economic',14_600,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'justice',         'Attorney-General Dept',    'Public Order & Safety',              6_700,   'BP1 2023-24 Statement 6'),
    ('2023-24', 'indigenous',      'NIAA',                     'Indigenous Affairs',                 5_400,   'BP1 2023-24 Statement 6'),
    ('2023-24', 'other',           'Various',                  'Other purposes / Public debt interest', 22_800, 'BP1 2023-24 Statement 6'),

    # ── 2024-25 ──
    ('2024-25', 'welfare',        'Services Australia',       'Social Security & Welfare',        266_700, 'BP1 2024-25 Statement 6'),
    ('2024-25', 'health',          'Dept Health',              'Health',                           117_400, 'BP1 2024-25 Statement 6'),
    ('2024-25', 'education',       'Dept Education',           'Education',                         50_300,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'defence',         'Dept Defence',             'Defence',                           45_900,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'infrastructure',  'Dept Infrastructure',      'Transport & Communications',        16_100,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'environment',     'Dept Climate & Energy',    'Fuel & Energy / Environment',       10_500,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'economy',         'Treasury',                 'General Public Services / Economic',15_300,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'justice',         'Attorney-General Dept',    'Public Order & Safety',              7_100,   'BP1 2024-25 Statement 6'),
    ('2024-25', 'indigenous',      'NIAA',                     'Indigenous Affairs',                 5_700,   'BP1 2024-25 Statement 6'),
    ('2024-25', 'other',           'Various',                  'Other purposes / Public debt interest', 26_400, 'BP1 2024-25 Statement 6'),

    # ── 2025-26 ──
    ('2025-26', 'welfare',        'Services Australia',       'Social Security & Welfare',        281_300, 'BP1 2025-26 Statement 6'),
    ('2025-26', 'health',          'Dept Health',              'Health',                           123_900, 'BP1 2025-26 Statement 6'),
    ('2025-26', 'education',       'Dept Education',           'Education',                         52_400,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'defence',         'Dept Defence',             'Defence',                           48_900,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'infrastructure',  'Dept Infrastructure',      'Transport & Communications',        16_800,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'environment',     'Dept Climate & Energy',    'Fuel & Energy / Environment',       11_200,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'economy',         'Treasury',                 'General Public Services / Economic',16_000,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'justice',         'Attorney-General Dept',    'Public Order & Safety',              7_500,   'BP1 2025-26 Statement 6'),
    ('2025-26', 'indigenous',      'NIAA',                     'Indigenous Affairs',                 6_000,   'BP1 2025-26 Statement 6'),
    ('2025-26', 'other',           'Various',                  'Other purposes / Public debt interest', 30_200, 'BP1 2025-26 Statement 6'),
]

# Additional federal spending lines that don't fit the 10 main sectors
# but make up a big chunk of the total. From Budget Paper No. 1, Statement 6.
# (year, sector, entity, program, amount_in_millions, source)
EXTRA_SPENDING = [
    # ── 2024-25 ──
    ('2024-25', 'other', 'Treasury',           'GST payments to states (FAGGs)',          90_500,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'other', 'Treasury',           'Specific Purpose Payments to states',     30_200,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'other', 'AOFM',               'Public debt interest',                    20_300,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'other', 'DFAT',               'Foreign aid & diplomacy',                  4_800,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'other', 'Various',            'Contingency reserve',                     12_000,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'other', 'Parliament',         'Parliament & Governor-General',            1_300,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'other', 'Various',            'Recreation, culture & religion',           4_200,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'other', 'Treasury',           'Housing, community amenities',             3_900,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'other', 'Various',            'Mining, manufacturing & construction',     5_100,  'BP1 2024-25 Statement 6'),
    ('2024-25', 'other', 'Various',            'Agriculture, forestry & fishing',          4_400,  'BP1 2024-25 Statement 6'),

    # ── 2025-26 ──
    ('2025-26', 'other', 'Treasury',           'GST payments to states (FAGGs)',          95_800,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'other', 'Treasury',           'Specific Purpose Payments to states',     32_100,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'other', 'AOFM',               'Public debt interest',                    23_500,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'other', 'DFAT',               'Foreign aid & diplomacy',                  5_000,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'other', 'Various',            'Contingency reserve',                     13_000,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'other', 'Parliament',         'Parliament & Governor-General',            1_350,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'other', 'Various',            'Recreation, culture & religion',           4_400,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'other', 'Treasury',           'Housing, community amenities',             4_100,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'other', 'Various',            'Mining, manufacturing & construction',     5_300,  'BP1 2025-26 Statement 6'),
    ('2025-26', 'other', 'Various',            'Agriculture, forestry & fishing',          4_500,  'BP1 2025-26 Statement 6'),

    # ── 2023-24 ──
    ('2023-24', 'other', 'Treasury',           'GST payments to states (FAGGs)',          85_300,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'other', 'Treasury',           'Specific Purpose Payments to states',     28_700,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'other', 'AOFM',               'Public debt interest',                    17_900,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'other', 'DFAT',               'Foreign aid & diplomacy',                  4_700,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'other', 'Various',            'Contingency reserve',                     10_500,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'other', 'Parliament',         'Parliament & Governor-General',            1_250,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'other', 'Various',            'Recreation, culture & religion',           4_100,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'other', 'Treasury',           'Housing, community amenities',             3_700,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'other', 'Various',            'Mining, manufacturing & construction',     4_900,  'BP1 2023-24 Statement 6'),
    ('2023-24', 'other', 'Various',            'Agriculture, forestry & fishing',          4_300,  'BP1 2023-24 Statement 6'),
]

SPENDING_DATA = SPENDING_DATA + EXTRA_SPENDING


def run():
    init_db()
    conn = get_conn()

    inserted = 0
    for year, sector, entity, program, amount_m, source in SPENDING_DATA:
        amount_aud = amount_m * 1_000_000
        h = hashlib.md5(f'BP1|{year}|{sector}|{entity}|{amount_m}'.encode()).hexdigest()
        try:
            conn.execute('''
                INSERT OR IGNORE INTO spending
                    (dataset_id, entity, program, sector, year, amount_aud, source_file, row_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('budget_paper', entity, program, sector, year, amount_aud, source, h))
            if conn.execute('SELECT changes()').fetchone()[0]:
                inserted += 1
        except Exception as e:
            print(f'  error: {e}')

    conn.commit()
    conn.close()
    print(f'✓ {inserted} sector totals seeded from Budget Papers.')
    print()
    print('Year totals now in DB:')
    conn = get_conn()
    rows = conn.execute('''
        SELECT year, COUNT(*), SUM(amount_aud)/1e9
        FROM spending
        WHERE source_file LIKE 'BP1%'
        GROUP BY year ORDER BY year
    ''').fetchall()
    for r in rows:
        print(f'  {r[0]}: {r[1]} sectors, ${r[2]:.1f}B total')
    conn.close()


if __name__ == '__main__':
    run()
