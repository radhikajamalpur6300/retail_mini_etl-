import sqlite3
from pathlib import Path

import pandas as pd

from src.etl import generate_synthetic_orders, load_data, transform_data, run_etl


def test_missing_quantity_filled_with_one(tmp_path: Path):
    raw_path = tmp_path / "data" / "raw" / "orders.csv"
    clean_path = tmp_path / "data" / "processed" / "orders_clean.csv"
    db_path = tmp_path / "db" / "orders.db"

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    generate_synthetic_orders(raw_path)

    df = transform_data(raw_path)
    assert df["quantity"].isna().sum() == 0
    assert (df.loc[df["order_id"].isin(["ORD005", "ORD011", "ORD017", "ORD023", "ORD029"]), "quantity"] == 1).all()

    load_data(df, clean_path, db_path)
    assert clean_path.exists()

    with sqlite3.connect(db_path) as conn:
        result = pd.read_sql_query("SELECT quantity FROM orders_clean", conn)
        assert (result["quantity"] == 1).sum() >= 5


def test_revenue_column_exists_and_non_negative(tmp_path: Path):
    raw_path = tmp_path / "data" / "raw" / "orders.csv"
    clean_path = tmp_path / "data" / "processed" / "orders_clean.csv"
    db_path = tmp_path / "db" / "orders.db"

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    generate_synthetic_orders(raw_path)

    df = transform_data(raw_path)
    assert "revenue" in df.columns
    assert (df["revenue"] >= 0).all()

    load_data(df, clean_path, db_path)
    with sqlite3.connect(db_path) as conn:
        result = pd.read_sql_query("SELECT revenue FROM orders_clean", conn)
        assert "revenue" in result.columns
        assert (result["revenue"] >= 0).all()


def test_run_etl_creates_clean_outputs(tmp_path: Path):
    raw_path = tmp_path / "data" / "raw" / "orders.csv"
    clean_path = tmp_path / "data" / "processed" / "orders_clean.csv"
    db_path = tmp_path / "db" / "orders.db"

    metrics = run_etl(raw_path=raw_path, clean_path=clean_path, db_path=db_path)

    assert clean_path.exists()
    assert db_path.exists()
    assert metrics["total_orders"] == 30
    assert metrics["total_revenue"] > 0
    assert metrics["top_product_by_revenue"] in generate_synthetic_orders(raw_path)["product"].unique()
