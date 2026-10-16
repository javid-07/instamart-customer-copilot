
from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")


def clean_orders():
    # Loading raw data.
    orders = pd.read_csv(RAW_DIR / "orders.csv")
    products = pd.read_csv(RAW_DIR / "products.csv")

    # 1. Convert order_ts to datetime.
    orders["order_ts"] = pd.to_datetime(orders["order_ts"])

    # 2. Remove exact duplicate rows.
    orders = orders.drop_duplicates()

    # 3. Keep the latest record for each order_id.
    orders = (
        orders.sort_values("order_ts")
        .drop_duplicates(subset="order_id", keep="last")
        .copy()
    )

    # 4. Convert order_amount to numeric.
    orders["order_amount"] = pd.to_numeric(
        orders["order_amount"], errors="coerce"
    )

    # Fill missing amounts using product price, quantity, and discount.
    product_prices = products[["product_id", "price_inr"]]
    orders = orders.merge(
        product_prices,
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    missing_amount = orders["order_amount"].isna()
    calculated_amount = (
        orders["price_inr"]
        * orders["quantity"]
        * (1 - orders["discount_pct"] / 100)
    ).round(2)

    orders.loc[missing_amount, "order_amount"] = calculated_amount[
        missing_amount
    ]

    orders = orders.drop(columns=["price_inr"])

    # 5. Treat negative delivery times as missing.
    orders.loc[orders["delivery_minutes"] < 0, "delivery_minutes"] = pd.NA

    # Add product category for category-level median calculation.
    orders = orders.merge(
        products[["product_id", "category"]],
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    completed = orders["status"].eq("completed")
    missing_completed = (
        completed & orders["delivery_minutes"].isna()
    )

    # Calculate medians from completed orders with valid delivery times.
    category_medians = (
        orders.loc[completed & orders["delivery_minutes"].notna()]
        .groupby("category")["delivery_minutes"]
        .median()
    )

    # Fill missing delivery times for completed orders only.
    orders.loc[missing_completed, "delivery_minutes"] = (
        orders.loc[missing_completed, "category"]
        .map(category_medians)
    )

    # Cancelled orders must retain missing delivery times.
    orders.loc[orders["status"].eq("cancelled"), "delivery_minutes"] = pd.NA

    # Remove the temporary category column.
    orders = orders.drop(columns=["category"])

    # Save the cleaned orders CSV.
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    orders["order_ts"] = orders["order_ts"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    orders.to_csv(CLEAN_DIR / "orders.csv", index=False)

    # Validate Task 3 reference checkpoints.
    completed_count = orders["status"].eq("completed").sum()
    cancelled_count = orders["status"].eq("cancelled").sum()
    pending_count = orders["status"].eq("pending").sum()
    missing_completed_delivery = (
        orders.loc[orders["status"].eq("completed"), "delivery_minutes"]
        .isna()
        .sum()
    )
    missing_cancelled_delivery = (
        orders.loc[orders["status"].eq("cancelled"), "delivery_minutes"]
        .isna()
        .sum()
    )
    completed_amount = orders.loc[
        orders["status"].eq("completed"), "order_amount"
    ].sum()

    print("Cleaned rows:", len(orders))
    print("Completed orders:", completed_count)
    print("Cancelled orders:", cancelled_count)
    print("Pending orders:", pending_count)
    print("Missing order_amount:", orders["order_amount"].isna().sum())
    print("Missing delivery on completed orders:", missing_completed_delivery)
    print("Missing delivery on cancelled orders:", missing_cancelled_delivery)
    print("Completed order amount total:", round(completed_amount, 2))


if __name__ == "__main__":
    clean_orders()
