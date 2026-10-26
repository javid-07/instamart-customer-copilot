
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ORDERS_PATH = ROOT / "data" / "clean" / "orders.csv"
CUSTOMERS_PATH = ROOT / "data" / "clean" / "customers.csv"
OUTPUT_PATH = ROOT / "outputs" / "lapse_dataset.csv"

CUTOFF = pd.Timestamp("2025-09-01")
LABEL_END = pd.Timestamp("2025-10-01")

orders = pd.read_csv(ORDERS_PATH)
customers = pd.read_csv(CUSTOMERS_PATH)

orders["order_ts"] = pd.to_datetime(orders["order_ts"], errors="coerce")
customers["signup_date"] = pd.to_datetime(
    customers["signup_date"], errors="coerce"
)

orders["status"] = orders["status"].str.lower()
completed = orders[orders["status"] == "completed"].copy()

# Only customers with a completed order before the cutoff enter the cohort.
pre_cutoff = completed[completed["order_ts"] < CUTOFF].copy()
cohort_ids = pre_cutoff["customer_id"].unique()

# Label: no completed order during September means lapsed = 1.
september_orders = completed[
    (completed["order_ts"] >= CUTOFF)
    & (completed["order_ts"] < LABEL_END)
]
active_in_september = set(september_orders["customer_id"])

labels = pd.DataFrame({"customer_id": cohort_ids})
labels["lapsed"] = (
    ~labels["customer_id"].isin(active_in_september)
).astype(int)

print("Cohort customers:", len(labels))
print("Lapsed customers:", int(labels["lapsed"].sum()))
print("Lapse rate (%):", round(labels["lapsed"].mean() * 100, 2))
print("Non-lapsed customers:", int((labels["lapsed"] == 0).sum()))

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
labels.to_csv(OUTPUT_PATH, index=False)
print(f"Saved: {OUTPUT_PATH.relative_to(ROOT)}")
