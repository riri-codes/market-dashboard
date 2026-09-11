"""
generate_insights.py
---------------------
Reads market_data.db and prints a short written summary: which assets were
most volatile, and which performed best/worst over the tracked window.

Run any time with:
    python generate_insights.py

The longer collector.py / the GitHub Action has been running, the more
meaningful this gets - with only a few snapshots it'll still run, but the
numbers won't mean much yet.
"""

import sqlite3
import pandas as pd

DB_PATH = "market_data.db"


def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM prices", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """For each symbol: first price, last price, % change over the whole
    window, and volatility (standard deviation of % changes between
    consecutive snapshots - a common simple volatility measure)."""
    rows = []
    for symbol, group in df.sort_values("timestamp").groupby("symbol"):
        first_price = group["price_usd"].iloc[0]
        last_price = group["price_usd"].iloc[-1]
        overall_pct_change = (last_price - first_price) / first_price * 100
        pct_changes = group["price_usd"].pct_change().dropna() * 100
        volatility = pct_changes.std() if len(pct_changes) > 1 else 0.0

        rows.append({
            "symbol": symbol,
            "asset_type": group["asset_type"].iloc[0],
            "first_price": first_price,
            "last_price": last_price,
            "overall_pct_change": overall_pct_change,
            "volatility": volatility,
            "snapshots": len(group),
        })
    return pd.DataFrame(rows)


def main():
    df = load_data()
    if df.empty:
        print("No data yet - run collector.py a few times first.")
        return

    summary = summarize(df)
    window_start = df["timestamp"].min()
    window_end = df["timestamp"].max()

    print("=" * 60)
    print("MARKET TRACKING - INSIGHTS SUMMARY")
    print("=" * 60)
    print(f"Tracking window: {window_start} to {window_end}")
    print(f"Total snapshots per asset (approx): {summary['snapshots'].mean():.0f}")
    print()

    best = summary.sort_values("overall_pct_change", ascending=False).iloc[0]
    worst = summary.sort_values("overall_pct_change", ascending=True).iloc[0]
    most_volatile = summary.sort_values("volatility", ascending=False).iloc[0]

    print(f"Best performer:  {best['symbol']}  ({best['overall_pct_change']:+.2f}%)")
    print(f"Worst performer: {worst['symbol']}  ({worst['overall_pct_change']:+.2f}%)")
    print(f"Most volatile:   {most_volatile['symbol']}  "
          f"(std dev of snapshot-to-snapshot % change: {most_volatile['volatility']:.2f}%)")
    print()

    print("Full breakdown:")
    print(
        summary[["symbol", "asset_type", "overall_pct_change", "volatility"]]
        .sort_values("overall_pct_change", ascending=False)
        .to_string(index=False, formatters={
            "overall_pct_change": "{:+.2f}%".format,
            "volatility": "{:.2f}%".format,
        })
    )


if __name__ == "__main__":
    main()
