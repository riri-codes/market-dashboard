"""
dashboard.py
------------
A Streamlit web dashboard that reads market_data.db (built by collector.py)
and shows live price charts for your tracked crypto + stocks.

Run with:
    streamlit run dashboard.py

This opens a browser tab. It auto-refreshes based on REFRESH_SECONDS below,
so leave collector.py (or loop_locally.py) running in another terminal and
watch the chart update.
"""

import sqlite3
import time

import pandas as pd
import streamlit as st

DB_PATH = "market_data.db"
REFRESH_SECONDS = 30

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Live Market Dashboard", layout="wide")
st.title("📈 Live Crypto & Stock Tracker")


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=REFRESH_SECONDS)
def load_data() -> pd.DataFrame:
    """Read the whole prices table into a pandas DataFrame.
    Cached for REFRESH_SECONDS so we're not hammering the DB on every
    Streamlit re-render, but it still refreshes on its own."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM prices", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


df = load_data()

if df.empty:
    st.warning("No data yet. Run collector.py a few times first.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

all_symbols = sorted(df["symbol"].unique())
selected_symbols = st.sidebar.multiselect(
    "Assets to show", options=all_symbols, default=all_symbols
)

st.sidebar.write(f"Total snapshots collected: {df['timestamp'].nunique()}")
st.sidebar.write(f"Last updated: {df['timestamp'].max()}")

filtered = df[df["symbol"].isin(selected_symbols)]

# ---------------------------------------------------------------------------
# Latest prices - quick glance metrics
# ---------------------------------------------------------------------------

st.subheader("Latest Prices")
latest = (
    filtered.sort_values("timestamp")
    .groupby("symbol")
    .tail(1)
    .sort_values("asset_type")
)

cols = st.columns(len(latest)) if len(latest) > 0 else []
for col, (_, row) in zip(cols, latest.iterrows()):
    col.metric(label=row["symbol"], value=f"${row['price_usd']:,.2f}")

# ---------------------------------------------------------------------------
# Price over time chart, one line per asset
# ---------------------------------------------------------------------------

st.subheader("Price Over Time")
pivot = filtered.pivot_table(index="timestamp", columns="symbol", values="price_usd")
st.line_chart(pivot)

# ---------------------------------------------------------------------------
# Raw data table (handy for debugging / sanity checks)
# ---------------------------------------------------------------------------

with st.expander("Raw data"):
    st.dataframe(filtered.sort_values("timestamp", ascending=False))

# ---------------------------------------------------------------------------
# Auto-refresh: reruns the whole script every REFRESH_SECONDS
# ---------------------------------------------------------------------------

time.sleep(REFRESH_SECONDS)
st.rerun()
