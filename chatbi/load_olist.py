"""Load Olist CSVs into chatbi/data/olist.db (Day 1).

Usage:
    python -m chatbi.load_olist --src Xiehaoyu-Agent/archive --db chatbi/data/olist.db
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


TABLE_MAP = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="Xiehaoyu-Agent/archive")
    parser.add_argument("--db", default="chatbi/data/olist.db")
    args = parser.parse_args()

    src = Path(args.src)
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")

    loaded = 0
    skipped = 0
    for csv_name, table in TABLE_MAP.items():
        csv_path = src / csv_name
        if not csv_path.exists():
            print(f"[skip] missing {csv_path}")
            skipped += 1
            continue
        df = pd.read_csv(csv_path)
        df.to_sql(table, engine, if_exists="replace", index=False)
        print(f"[ok] {csv_name} -> {table} ({len(df)} rows)")
        loaded += 1

    print(f"\nDone: {loaded} loaded, {skipped} skipped")
    if loaded == 0:
        print("[ERROR] No tables were loaded. Check that --src points to the Olist CSV directory.")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
