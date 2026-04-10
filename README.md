# AusSpend — Australian Government Spending Tracker

A public-facing dashboard that pulls Australian federal budget data from official
sources and presents it in plain English. Built with React + Vite (frontend) and
Flask + SQLite (backend).

> **Independent open-data project — not affiliated with the Australian Government.**

## What's tracked

- **Federal Spending** — sector totals from Budget Paper No. 1 (2020–2026)
- **Federal Revenue** — tax & non-tax income from Budget Paper No. 1 (2021–2026)
- **240,000 individual contracts** from AusTender (2014–2019)
- **National Debt** — Commonwealth Government Securities from AOFM
- **HECS/HELP** — student loan book figures

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | React 19 + Vite + CSS Modules |
| Backend | Python 3 + Flask + SQLite |
| Data ingest | Python scripts (requests, pandas) |

## Quick start

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+

### 1. Clone and install

```bash
git clone https://github.com/YOUR-USERNAME/ausspend.git
cd ausspend

# Frontend
npm install

# Backend
cd backend
bash setup.sh        # creates venv, installs deps, initialises DB
cd ..
```

### 2. Load the data

Data files aren't in the repo (too large). Run the ingest scripts to populate
your local database:

```bash
cd backend

# Seed authoritative figures from Budget Papers
.venv/bin/python3 seed_revenue.py
.venv/bin/python3 seed_spending.py

# Optional: pull individual contract data from data.gov.au
.venv/bin/python3 fetch_data_gov.py
.venv/bin/python3 parse_spending.py

.venv/bin/python3 fetch_contracts.py
.venv/bin/python3 parse_contracts.py
```

### 3. Run

You need two terminals:

**Terminal 1 — Backend:**
```bash
cd backend
.venv/bin/python3 api.py
```

**Terminal 2 — Frontend:**
```bash
npm run dev
```

Open <http://localhost:5173>.

## Project structure

```
ausspend/
├── src/                    # React frontend
│   ├── components/         # Reusable UI components
│   ├── pages/              # Dashboard, Spending, Revenue, Debt, Scope, Sources
│   ├── data.js             # Sector definitions (colours, descriptions)
│   ├── App.jsx             # Routing & shared state
│   └── main.jsx
├── backend/                # Python API
│   ├── api.py              # Flask app
│   ├── db.py               # SQLite schema
│   ├── seed_*.py           # Hardcoded Budget Paper figures
│   ├── fetch_*.py          # Data downloaders
│   ├── parse_*.py          # File parsers
│   └── data/               # SQLite DB + raw files (gitignored)
├── public/
├── nginx.conf              # Production nginx config
└── vite.config.js
```

## Data sources

| Data | Source | Method |
|---|---|---|
| Sector totals | budget.gov.au — Budget Paper No. 1 | Hardcoded from PDFs |
| Revenue | budget.gov.au — Statement 5 | Hardcoded from PDFs |
| Contracts | tenders.gov.au via data.gov.au | CKAN API |
| National Debt | aofm.gov.au/statistics | Direct CSV download |
| HECS/HELP | education.gov.au | Hardcoded context figures |

All sources are official Australian Government publications. See the in-app
**Sources** page for the full list with direct links.

## Deploying to production

The frontend is a static site after `npm run build` — works behind nginx,
Cloudflare Pages, GitHub Pages, etc.

```bash
npm run build       # outputs to dist/
```

For a Linux/Proxmox VM with nginx, see [nginx.conf](nginx.conf) for an example
config that serves the static frontend and proxies `/api/*` to the Flask backend.

## Limitations

- **2020+ contract detail** is missing — the AusTender bulk exports on data.gov.au
  stopped being updated in 2019, and the live AusTender system blocks automated tools.
  Headline figures come from Budget Papers instead.
- **Federal only** — state taxes (rego, stamp duty, land tax) and council rates
  aren't tracked. See the in-app **Data Scope** page for the full breakdown.
- **Estimates vs actuals** — Budget Paper figures are estimates published in May.
  Final Budget Outcome documents (published each September) are the settled figures
  and may differ slightly.

## Contributing

This is a personal project but pull requests are welcome — especially for:
- State / territory data ingest scripts
- Better PDF parsing for Budget Papers
- News enrichment (mapping spending to news coverage)

## License

MIT — use it however you like. Attribution appreciated but not required.
