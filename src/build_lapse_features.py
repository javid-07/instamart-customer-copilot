
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ORDERS_PATH = ROOT / "data" / "clean" / "orders.csv"
CUSTOMERS_PATH = ROOT / "data" / "clean" / "customers.csv"
LABELS_PATH = ROOT / "outputs" / "lapse_dataset.csv"
OUTPUT_PATH = ROOT / "outputs" / "lapse_features.csv"

CUTOFF = pd.Timestamp("2025-09-01")

orders = pd.read_csv(ORDERS_PATH)
customers = pd.read_csv(CUSTOMERS_PATH)
labels = pd.read_csv(LABELS_PATH)

orders["order_ts"] = pd.to_datetime(orders["order_ts"], errors="coerce")
customers["signup_date"] = pd.to_datetime(
    customers["signup_date"], errors="coerce"
)
orders["status"] = orders["status"].str.lower()

# Strictly exclude orders on or after the cutoff from features.
pre = orders[orders["order_ts"] < CUTOFF].copy()
completed = pre[pre["status"] == "completed"].copy()

# Cohort is determined by completed orders before cutoff.
cohort_ids = set(labels["customer_id"])
completed = completed[completed["customer_id"].isin(cohort_ids)]
pre = pre[pre["customer_id"].isin(cohort_ids)]

# Completed-order behaviour features.
rfm = (
    completed.groupby("customer_id")
    .agg(
        last_order_ts=("order_ts", "max"),
        frequency=("order_id", "nunique"),
        monetary=("order_amount", "sum"),
        avg_discount_pct=("discount_pct", "mean"),
        avg_delivery_minutes=("delivery_minutes", "mean"),
    )
    .reset_index()
)
rfm["recency"] = (CUTOFF - rfm["last_order_ts"]).dt.days
rfm = rfm.drop(columns="last_order_ts")

# Cancellation rate: cancelled / all orders with a final status.
final_orders = pre[pre["status"].isin(["completed", "cancelled"])]
status_counts = (
    final_orders.assign(is_cancelled=final_orders["status"].eq("cancelled"))
    .groupby("customer_id")
    .agg(
        total_final_orders=("order_id", "nunique"),
        cancelled_orders=("is_cancelled", "sum"),
    )
    .reset_index()
)
status_counts["cancellation_rate"] = (
    status_counts["cancelled_orders"] / status_counts["total_final_orders"]
)

# Most frequent product category, using completed orders before cutoff.
category_orders = completed.merge(
    pd.read_csv(ROOT / "data" / "clean" / "products.csv")[
        ["product_id", "category"]
    ],
    on="product_id",
    how="left",
)
favourite_category = (
    category_orders.groupby(["customer_id", "category"])
    .size()
    .reset_index(name="category_orders")
    .sort_values(
        ["customer_id", "category_orders", "category"],
        ascending=[True, False, True],
    )
    .drop_duplicates("customer_id")
    [["customer_id", "category"]]
    .rename(columns={"category": "favourite_category"})
)

# Customer attributes and tenure at cutoff.
customer_features = customers[
    ["customer_id", "city", "age", "gender", "signup_date"]
].copy()
customer_features["tenure_days"] = (
    CUTOFF - customer_features["signup_date"]
).dt.days
customer_features = customer_features.drop(columns="signup_date")

features = (
    labels[["customer_id", "lapsed"]]
    .merge(rfm, on="customer_id", how="left")
    .merge(status_counts[["customer_id", "cancellation_rate"]],
           on="customer_id", how="left")
    .merge(favourite_category, on="customer_id", how="left")
    .merge(customer_features, on="customer_id", how="left")
)

# Assert the feature table contains no missing values.
missing = features.isna().sum()
print("Missing values by column:")
print(missing[missing > 0].to_string() if missing.any() else "None")

if features.isna().any().any():
    raise ValueError(
        "Missing feature values found. Inspect the columns above before modeling."
    )

# Leakage guard: labels are kept as target, never as feature inputs.
features.to_csv(OUTPUT_PATH, index=False)

print("\nFeature dataset shape:", features.shape)
print("Lapsed count:", int(features["lapsed"].sum()))
print("Feature columns:", [c for c in features.columns if c not in {
    "customer_id", "lapsed"
}])
print(f"Saved: {OUTPUT_PATH.relative_to(ROOT)}")
