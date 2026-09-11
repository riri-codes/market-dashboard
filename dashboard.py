"""
dashboard.py
------------
A Streamlit web dashboard that reads market_data.db (built by collector.py)
and shows live price charts, rolling averages, and volatility alerts for
your tracked crypto + stocks.

Run with:
    streamlit run dashboard.py
"""

import sqlite3
import time

import pandas as pd
import streamlit as st

DB_PATH = "market_data.db"
REFRESH_SECONDS = 30

# How many rows to average over for the "short" and "long" rolling windows.
# These are in NUMBER OF SNAPSHOTS, not minutes - e.g. if you collect every
# 5 minutes, a window of 12 rows = roughly 1 hour.
SHORT_WINDOW = 3
LONG_WINDOW = 12

# Flag a snapshot-to-snapshot move bigger than this as a volatility spike.
SPIKE_THRESHOLD_PCT = 5.0

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
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM prices", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def add_analysis_columns(df: pd.DataFrame) -> pd.DataFrame:
    """For each asset (symbol), sorted by time, add:
    - rolling short/long averages
    - % change from the previous snapshot
    - a boolean flag for whether that change counts as a 'spike'
    """
    df = df.sort_values(["symbol", "timestamp"]).copy()

    def per_symbol(group: pd.DataFrame) -> pd.DataFrame:
        group = group.copy()
        group["short_ma"] = group["price_usd"].rolling(SHORT_WINDOW, min_periods=1).mean()
        group["long_ma"] = group["price_usd"].rolling(LONG_WINDOW, min_periods=1).mean()
        group["pct_change"] = group["price_usd"].pct_change() * 100
        group["is_spike"] = group["pct_change"].abs() >= SPIKE_THRESHOLD_PCT
        return group

    return df.groupby("symbol", group_keys=False).apply(per_symbol)


df = load_data()

if df.empty:
    st.warning("No data yet. Run collector.py a few times first.")
    st.stop()

df = add_analysis_columns(df)

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

all_symbols = sorted(df["symbol"].unique())
selected_symbols = st.sidebar.multiselect(
    "Assets to show", options=all_symbols, default=all_symbols
)

st.sidebar.write(f"Total snapshots collected: {df['timestamp'].nunique()}")
st.sidebar.write(f"Last updated: {df['timestamp'].max()}")
st.sidebar.caption(
    f"Rolling averages: short = last {SHORT_WINDOW} snapshots, "
    f"long = last {LONG_WINDOW} snapshots. "
    f"Spike alert threshold: {SPIKE_THRESHOLD_PCT}% move between snapshots."
)

filtered = df[df["symbol"].isin(selected_symbols)]

# ---------------------------------------------------------------------------
# Latest prices + % change - quick glance metrics
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
    delta = None if pd.isna(row["pct_change"]) else f"{row['pct_change']:.2f}%"
    col.metric(label=row["symbol"], value=f"${row['price_usd']:,.4f}", delta=delta)

# ---------------------------------------------------------------------------
# Volatility spike alerts
# ---------------------------------------------------------------------------

st.subheader("⚠️ Volatility Alerts")
spikes = filtered[filtered["is_spike"]].sort_values("timestamp", ascending=False)
if spikes.empty:
    st.info(f"No moves ≥ {SPIKE_THRESHOLD_PCT}% between snapshots yet.")
else:
    st.dataframe(
        spikes[["timestamp", "symbol", "price_usd", "pct_change"]]
        .rename(columns={"pct_change": "% change"})
        .style.format({"price_usd": "${:,.4f}", "% change": "{:+.2f}%"})
    )

# ---------------------------------------------------------------------------
# Price + rolling averages chart, one asset at a time (keeps lines readable)
# ---------------------------------------------------------------------------

st.subheader("Price Over Time (with rolling averages)")
chart_symbol = st.selectbox("Choose an asset to chart in detail", options=all_symbols)
single = filtered[filtered["symbol"] == chart_symbol].set_index("timestamp")
st.line_chart(single[["price_usd", "short_ma", "long_ma"]])

st.subheader("All Assets - Raw Price Comparison")
pivot = filtered.pivot_table(index="timestamp", columns="symbol", values="price_usd")
st.line_chart(pivot)

# ---------------------------------------------------------------------------
# Raw data table
# ---------------------------------------------------------------------------

with st.expander("Raw data"):
    st.dataframe(filtered.sort_values("timestamp", ascending=False))

# ---------------------------------------------------------------------------
# Auto-refresh
# ---------------------------------------------------------------------------

time.sleep(REFRESH_SECONDS)
st.rerun()
