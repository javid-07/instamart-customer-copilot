
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")


def audit_table(filename):
    path = RAW_DIR / filename

    # Preserve blank ticket text as empty strings when auditing tickets.
    if filename == "tickets.csv":
        df = pd.read_csv(path, keep_default_na=False)
    else:
        df = pd.read_csv(path)

    print("\n" + "=" * 60)
    print(f"FILE: {filename}")
    print(f"Shape: {df.shape}")

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    missing = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_percentage": (df.isna().mean() * 100).round(2)
    })
    print(missing)

    print("\nExact duplicate rows:", df.duplicated().sum())

    return df


customers = audit_table("customers.csv")
products = audit_table("products.csv")
orders = audit_table("orders.csv")

print("\n" + "=" * 60)
print("SPECIFIC AUDIT FIGURES")

print("\nORDERS")
print("Raw orders rows:", len(orders))
print("Exact duplicate rows:", orders.duplicated().sum())
print("Pending rows:", orders["status"].eq("pending").sum())
print("Distinct order_id values:", orders["order_id"].nunique())

amount_numeric = pd.to_numeric(orders["order_amount"], errors="coerce")
print(
    "Non-numeric order_amount entries:",
    amount_numeric.isna().sum()
)
print("Negative delivery_minutes:", orders["delivery_minutes"].lt(0).sum())
print(
    "Blank delivery_minutes:",
    orders["delivery_minutes"].astype("string").str.strip().eq("").sum()
    + orders["delivery_minutes"].isna().sum()
)

print("\nCUSTOMERS")
print("Blank age:", customers["age"].isna().sum())
print(
    "Age values outside 10-100:",
    ((customers["age"] < 10) | (customers["age"] > 100)).sum()
)
print("Distinct raw city spellings:", customers["city"].nunique())
print(
    "Distinct non-blank raw gender spellings:",
    customers.loc[
        customers["gender"].astype("string").str.strip().ne(""),
        "gender"
    ].nunique()
)
print(
    "Blank gender:",
    customers["gender"].astype("string").str.strip().eq("").sum()
    + customers["gender"].isna().sum()
)
