
from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")


def clean_customers():
    customers = pd.read_csv(RAW_DIR / "customers.csv")

    # 1. Standardize city names
    customers["city"] = (
        customers["city"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # 2. Standardize gender values
    gender = customers["gender"].astype("string").str.strip().str.lower()

    gender_mapping = {
        "m": "male",
        "male": "male",
        "man": "male",
        "f": "female",
        "female": "female",
        "woman": "female",
    }

    customers["gender"] = gender.map(gender_mapping).fillna("unknown")

    # 3. Convert invalid ages to missing, then fill by city median
    customers["age"] = pd.to_numeric(
        customers["age"], errors="coerce"
    )

    invalid_age = (
        customers["age"].notna()
        & ~customers["age"].between(10, 100)
    )
    customers.loc[invalid_age, "age"] = pd.NA

    city_median_age = customers.groupby("city")["age"].transform("median")
    customers["age"] = customers["age"].fillna(city_median_age)

    # 4. Convert signup_date to datetime
    customers["signup_date"] = pd.to_datetime(
        customers["signup_date"], errors="coerce"
    )

    # Save the cleaned customers CSV
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    customers["signup_date"] = customers["signup_date"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    customers.to_csv(CLEAN_DIR / "customers.csv", index=False)

    # Validate reference checkpoints
    print("Cleaned customer rows:", len(customers))
    print("\nCity counts:")
    print(customers["city"].value_counts().sort_index())

    print("\nGender counts:")
    print(customers["gender"].value_counts().sort_index())

    print("\nMissing ages:", customers["age"].isna().sum())
    print("Minimum age:", customers["age"].min())
    print("Maximum age:", customers["age"].max())
    print("Missing signup dates:", customers["signup_date"].isna().sum())


if __name__ == "__main__":
    clean_customers()
