
from pathlib import Path

import pandas as pd

# Project paths
ROOT = Path(__file__).resolve().parent.parent
ORDERS_PATH = ROOT / "data" / "clean" / "orders.csv"
OUTPUT_PATH = ROOT / "outputs" / "rfm.csv"

# Snapshot moment from the assignment
SNAPSHOT_DATE = pd.Timestamp("2025-10-01 00:00:00")

# Load cleaned orders
orders = pd.read_csv(ORDERS_PATH)

# Parse order timestamps
orders["order_ts"] = pd.to_datetime(orders["order_ts"], errors="coerce")

# Use completed orders only
completed = orders.loc[orders["status"].str.lower().eq("completed")].copy()

# Build RFM for customers with at least one completed order
rfm = (
    completed.groupby("customer_id")
    .agg(
        last_order_ts=("order_ts", "max"),
        frequency=("order_id", "nunique"),
        monetary=("order_amount", "sum"),
    )
    .reset_index()
)

# Recency: whole days from last completed order to snapshot
rfm["recency"] = (SNAPSHOT_DATE - rfm["last_order_ts"]).dt.days

# Keep required column order
rfm = rfm[
    ["customer_id", "recency", "frequency", "monetary", "last_order_ts"]
]

# Save output
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
rfm.to_csv(OUTPUT_PATH, index=False)

# Print reference checks
print(f"RFM customers: {len(rfm)}")
print(f"Recency median: {rfm['recency'].median():.0f}")
print(f"Recency minimum: {rfm['recency'].min()}")
print(f"Recency maximum: {rfm['recency'].max()}")
print(f"Frequency mean: {rfm['frequency'].mean():.2f}")
print(f"Frequency maximum: {rfm['frequency'].max()}")
print(f"Monetary mean: {rfm['monetary'].mean():,.2f}")
print(f"Monetary maximum: {rfm['monetary'].max():,.2f}")
print(f"Saved: {OUTPUT_PATH.relative_to(ROOT)}")
