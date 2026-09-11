"""
collector.py
------------
Pulls one "snapshot" of prices for a list of crypto coins (via CoinGecko)
and stocks (via yfinance), and saves them into a SQLite database.

Run this file directly to take ONE snapshot:
    python collector.py

To collect continuously while testing locally, see loop_locally.py
(for real 24/7 collection, we'll automate this with GitHub Actions later).
"""

import sqlite3
import requests
import yfinance as yf
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1. CONFIG - edit these lists to track whatever assets you want
# ---------------------------------------------------------------------------

CRYPTO_IDS = ["bitcoin", "ethereum", "solana", "dogecoin"]   # CoinGecko IDs
STOCK_TICKERS = ["AAPL", "MSFT", "TSLA", "NVDA"]             # Yahoo Finance tickers

DB_PATH = "market_data.db"

# ---------------------------------------------------------------------------
# 2. DATABASE SETUP
# ---------------------------------------------------------------------------

def init_db(db_path: str = DB_PATH):
    """Create the prices table if it doesn't exist yet.
    One row = one asset's price at one point in time."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type  TEXT NOT NULL,   -- 'crypto' or 'stock'
            symbol      TEXT NOT NULL,   -- e.g. 'bitcoin' or 'AAPL'
            price_usd   REAL NOT NULL,
            timestamp   TEXT NOT NULL    -- ISO format UTC timestamp
        )
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# 3. FETCHERS
# ---------------------------------------------------------------------------

def fetch_crypto_prices(coin_ids: list[str]) -> dict[str, float]:
    """Query CoinGecko's simple price endpoint. No API key needed."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": "usd",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    # data looks like: {"bitcoin": {"usd": 61234.5}, "ethereum": {"usd": 3011.2}}
    return {coin: values["usd"] for coin, values in data.items()}


def fetch_stock_prices(tickers: list[str]) -> dict[str, float]:
    """Query Yahoo Finance for the latest available price per ticker."""
    prices = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            # fast_info is quick and avoids pulling full historical data
            price = t.fast_info["last_price"]
            prices[ticker] = float(price)
        except Exception as e:
            print(f"  [warn] could not fetch {ticker}: {e}")
    return prices


# ---------------------------------------------------------------------------
# 4. MAIN COLLECTION FUNCTION
# ---------------------------------------------------------------------------

def collect_once(db_path: str = DB_PATH):
    """Fetch current crypto + stock prices and insert them as new rows."""
    conn = init_db(db_path)
    timestamp = datetime.now(timezone.utc).isoformat()

    rows_added = 0

    try:
        crypto_prices = fetch_crypto_prices(CRYPTO_IDS)
        for symbol, price in crypto_prices.items():
            conn.execute(
                "INSERT INTO prices (asset_type, symbol, price_usd, timestamp) VALUES (?, ?, ?, ?)",
                ("crypto", symbol, price, timestamp),
            )
            rows_added += 1
    except Exception as e:
        print(f"  [error] crypto fetch failed: {e}")

    try:
        stock_prices = fetch_stock_prices(STOCK_TICKERS)
        for symbol, price in stock_prices.items():
            conn.execute(
                "INSERT INTO prices (asset_type, symbol, price_usd, timestamp) VALUES (?, ?, ?, ?)",
                ("stock", symbol, price, timestamp),
            )
            rows_added += 1
    except Exception as e:
        print(f"  [error] stock fetch failed: {e}")

    conn.commit()
    conn.close()
    print(f"[{timestamp}] Collected {rows_added} rows -> {db_path}")
    return rows_added


if __name__ == "__main__":
    collect_once()
