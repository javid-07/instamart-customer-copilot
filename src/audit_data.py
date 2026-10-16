from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")

files = ["customers.csv", "products.csv", "orders.csv"]

for filename in files:
    path = RAW_DIR / filename
    df = pd.read_csv(path)

    print(f"\n{'=' * 50}")
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