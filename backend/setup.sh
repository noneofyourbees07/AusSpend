#!/bin/bash
# One-time setup script for the AusSpend backend.
# Run: bash setup.sh

set -e

echo "── Creating Python virtual environment ──"
python3 -m venv .venv

echo "── Installing dependencies ──"
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo "── Initialising database ──"
.venv/bin/python3 db.py

echo ""
echo "✓ Setup complete. Next steps:"
echo ""
echo "  1. Fetch data from data.gov.au:"
echo "     .venv/bin/python3 fetch_data_gov.py"
echo ""
echo "  2. Parse downloaded files into the database:"
echo "     .venv/bin/python3 parse_spending.py"
echo ""
echo "  3. Start the API server:"
echo "     .venv/bin/python3 api.py"
echo ""
