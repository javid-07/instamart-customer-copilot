import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "instamart.db"

conn = sqlite3.connect(DB_PATH)

orders = pd.read_sql_query(
    "SELECT * FROM orders WHERE status = 'completed'",
    conn
)

customers = pd.read_sql_query(
    "SELECT * FROM customers",
    conn
)

products = pd.read_sql_query(
    "SELECT * FROM products",
    conn
)

conn.close()

print("Completed orders:", len(orders))
print("Customers:", len(customers))
print("Products:", len(products))

# Part A: Pandas cross-check — Q2 revenue by city and category

orders_with_details = (
    orders
    .merge(customers[["customer_id", "city"]], on="customer_id", how="left")
    .merge(products[["product_id", "category"]], on="product_id", how="left")
)

pivot = pd.pivot_table(
    orders_with_details,
    values="order_amount",
    index="city",
    columns="category",
    aggfunc="sum",
    fill_value=0,
    margins=True,
    margins_name="All"
)

print("\nRevenue pivot table (INR):")
print(pivot.round(2))

pivot_total = pivot.loc["All", "All"]
print("\nPandas pivot grand total:", round(pivot_total, 2))

# City-wise completed order statistics

city_stats = (
    orders_with_details
    .groupby("city")
    .agg(
        total_revenue=("order_amount", "sum"),
        mean_order_amount=("order_amount", "mean"),
        order_count=("order_amount", "count")
    )
    .round(2)
    .reset_index()
)

print("\nCity-wise completed order statistics:")
print(city_stats.to_string(index=False))

# Distribution statistics and IQR outlier analysis

amount = orders["order_amount"]

q1 = amount.quantile(0.25)
median = amount.median()
q3 = amount.quantile(0.75)
iqr = q3 - q1

lower_fence = q1 - 1.5 * iqr
upper_fence = q3 + 1.5 * iqr

print("\nCompleted order amount distribution (INR):")
print("Mean:", round(amount.mean(), 2))
print("Median:", round(median, 2))
print("Skewness:", round(amount.skew(), 2))
print("Q1:", round(q1, 2))
print("Q3:", round(q3, 2))
print("IQR:", round(iqr, 2))
print("Lower fence:", round(lower_fence, 2))
print("Upper fence:", round(upper_fence, 2))
print("Outliers below lower fence:", int((amount < lower_fence).sum()))
print("Outliers above upper fence:", int((amount > upper_fence).sum()))

# Correlation matrix for completed orders

correlation_columns = [
    "order_amount",
    "discount_pct",
    "quantity",
    "delivery_minutes"
]

correlation_matrix = orders[correlation_columns].corr()

print("\nCorrelation matrix:")
print(correlation_matrix.round(3))

# Find the pair with the largest absolute correlation
abs_corr = correlation_matrix.abs()
pairs = abs_corr.where(
    ~pd.DataFrame(
        [[i == j for j in range(len(abs_corr.columns))]
         for i in range(len(abs_corr.columns))],
        index=abs_corr.index,
        columns=abs_corr.columns
    )
).stack()

strongest_pair = pairs.idxmax()
signed_value = correlation_matrix.loc[
    strongest_pair[0], strongest_pair[1]
]

print("\nLargest absolute correlation pair:", strongest_pair)
print("Correlation coefficient:", round(signed_value, 3))