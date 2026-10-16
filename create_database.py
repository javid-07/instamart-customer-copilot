import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CLEAN_DIR = DATA_DIR / "clean"
DB_PATH = DATA_DIR / "instamart.db"

conn = sqlite3.connect(DB_PATH)

tables = ["customers", "products", "orders"]

for table in tables:
    csv_path = CLEAN_DIR / f"{table}.csv"
    df = pd.read_csv(csv_path)

    if table == "orders":
        df["order_ts"] = pd.to_datetime(df["order_ts"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    df.to_sql(table, conn, if_exists="replace", index=False)
    print(f"{table}: {len(df)} rows loaded")

conn.close()

print("All clean tables loaded into SQLite.")