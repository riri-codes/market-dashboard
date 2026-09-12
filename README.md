# Live Crypto & Stock Market Tracking Dashboard

A live-updating dashboard that tracks cryptocurrency and stock prices in
real time, stores the historical data, and surfaces volatility alerts and
trend analysis - fully automated and hosted for free.

**Live dashboard:** https://market-dashboard-h8c3lkcljmxgrk9exydqbm.streamlit.app

## What it does

- Pulls live prices every 15 minutes for a mix of crypto (via the CoinGecko
  API) and stocks (via Yahoo Finance)
- Stores every snapshot in a growing SQLite database, building a real
  historical dataset over time
- Displays the data on a live web dashboard with:
  - Current prices and % change since the last snapshot
  - Short/long rolling averages to smooth out noise
  - Automatic alerts when an asset moves more than 5% between snapshots
- Generates a written summary (best/worst performer, most volatile asset)
  from the collected history

## Architecture

```
GitHub Actions (cron, every 15 min)
        |
        v
  collector.py  --> pulls prices from CoinGecko + yfinance
        |
        v
  market_data.db (SQLite, committed back to this repo)
        |
        v
  dashboard.py  --> Streamlit app, deployed on Streamlit Community Cloud
        |
        v
  generate_insights.py --> run locally for a written performance summary
```

Data collection runs entirely in GitHub Actions, so the dashboard keeps
updating even when no one's laptop is on. The dashboard auto-redeploys
whenever this repo changes.

## Files

| File | Purpose |
|---|---|
| `collector.py` | Fetches current prices and inserts them into the database |
| `dashboard.py` | Streamlit app - the live dashboard |
| `generate_insights.py` | Prints a written performance/volatility summary |
| `loop_locally.py` | Optional - runs the collector on a loop for local testing |
| `.github/workflows/collect.yml` | GitHub Actions workflow that automates collection |
| `requirements.txt` | Python dependencies |

## Running it yourself

```bash
pip install -r requirements.txt
python collector.py          # take one price snapshot
streamlit run dashboard.py   # view the dashboard locally
python generate_insights.py  # print the written summary
```

## Tech stack

Python, SQLite, Streamlit, GitHub Actions, CoinGecko API, yfinance
