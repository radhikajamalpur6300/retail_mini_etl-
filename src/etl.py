import sqlite3
from pathlib import Path

import pandas as pd

RAW_CSV = Path("data/raw/orders.csv")
CLEAN_CSV = Path("data/processed/orders_clean.csv")
DB_PATH = Path("db/orders.db")
TABLE_NAME = "orders_clean"


def generate_synthetic_orders(path: Path = RAW_CSV) -> pd.DataFrame:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    products = ["Widget", "Gadget", "Doohickey", "Thingamajig", "Whatchamacallit"]
    rows = []

    for i in range(1, 31):
        order_id = f"ORD{i:03d}"
        order_date = (pd.to_datetime("2026-01-01") + pd.Timedelta(days=i - 1)).strftime("%Y-%m-%d")
        product = products[i % len(products)]
        unit_price = float(5 + (i % 10) * 1.5)
        quantity = "" if i in {5, 11, 17, 23, 29} else (i % 5) + 1

        rows.append(
            {
                "order_id": order_id,
                "order_date": order_date,
                "product": product,
                "quantity": quantity,
                "unit_price": unit_price,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return df


def transform_data(raw_path: Path | str = RAW_CSV) -> pd.DataFrame:
    raw_path = Path(raw_path)
    if not raw_path.exists():
        generate_synthetic_orders(raw_path)

    df = pd.read_csv(raw_path)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").astype(float)
    df["revenue"] = df["quantity"] * df["unit_price"]
    return df


def load_data(df: pd.DataFrame, clean_path: Path = CLEAN_CSV, db_path: Path = DB_PATH) -> None:
    clean_path = Path(clean_path)
    db_path = Path(db_path)
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(clean_path, index=False)
    with sqlite3.connect(db_path) as conn:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)


def print_kpis(df: pd.DataFrame) -> dict[str, object]:
    total_orders = int(len(df))
    total_revenue = float(df["revenue"].sum())
    top_product_by_revenue = df.groupby("product")["revenue"].sum().idxmax()

    print(f"total_orders: {total_orders}")
    print(f"total_revenue: {total_revenue:.2f}")
    print(f"top_product_by_revenue: {top_product_by_revenue}")

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_product_by_revenue": top_product_by_revenue,
    }


def run_etl(
    raw_path: Path | str = RAW_CSV,
    clean_path: Path | str = CLEAN_CSV,
    db_path: Path | str = DB_PATH,
) -> dict[str, object]:
    df = transform_data(raw_path)
    load_data(df, clean_path, db_path)
    return print_kpis(df)


if __name__ == "__main__":
    run_etl()
