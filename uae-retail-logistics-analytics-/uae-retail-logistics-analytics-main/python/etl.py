"""
etl.py
------
Loads the generated CSV files into a SQLite database, applying the schema
defined in sql/01_schema.sql. This mimics a lightweight ETL pipeline:
Extract (CSV) -> Transform (dtype handling) -> Load (SQLite).
"""

import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
SQL_DIR = os.path.join(BASE_DIR, "sql")
DB_PATH = os.path.join(DATA_DIR, "uae_retail.db")


def main():
    # Fresh DB each run
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Apply schema
    with open(os.path.join(SQL_DIR, "01_schema.sql"), "r") as f:
        cur.executescript(f.read())
    conn.commit()

    # 2. Load each CSV into its matching table
    tables = [
        ("customers", "customers.csv"),
        ("suppliers", "suppliers.csv"),
        ("products", "products.csv"),
        ("warehouses", "warehouses.csv"),
        ("orders", "orders.csv"),
        ("order_items", "order_items.csv"),
        ("deliveries", "deliveries.csv"),
    ]

    for table_name, file_name in tables:
        df = pd.read_csv(os.path.join(DATA_DIR, file_name))
        df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"Loaded {len(df):,} rows into '{table_name}'")

    conn.close()
    print(f"\nSQLite database ready at: {DB_PATH}")


if __name__ == "__main__":
    main()
