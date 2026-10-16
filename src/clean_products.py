
from pathlib import Path

import pandas as pd


RAW_FILE = Path("data/raw/products.csv")
CLEAN_DIR = Path("data/clean")
OUTPUT_FILE = CLEAN_DIR / "products.csv"


def clean_products():
    products = pd.read_csv(RAW_FILE)

    # Validate the required columns and data.
    required_columns = [
        "product_id",
        "product_name",
        "category",
        "price_inr",
    ]
    assert list(products.columns) == required_columns
    assert products["product_id"].is_unique
    assert products.isna().sum().sum() == 0
    assert products["price_inr"].gt(0).all()

    # No cleaning transformations are required for this dataset.
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    products.to_csv(OUTPUT_FILE, index=False)

    print("Cleaned product rows:", len(products))
    print("Unique product IDs:", products["product_id"].nunique())
    print("Missing values:", products.isna().sum().sum())
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    clean_products()
