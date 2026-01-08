from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db" / "olist.db"
DATA_DIR = PROJECT_ROOT / "data"

def create_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_tables(conn: sqlite3.Connection):
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            customer_unique_id TEXT,
            customer_zip_code_prefix INTEGER,
            customer_city TEXT,
            customer_state TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT,
            order_status TEXT,
            order_purchase_timestamp TEXT,
            order_approved_at TEXT,
            order_delivered_carrier_date TEXT,
            order_delivered_customer_date TEXT,
            order_estimated_delivery_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_id TEXT,
            order_item_id INTEGER,
            product_id TEXT,
            seller_id TEXT,
            shipping_limit_date TEXT,
            price REAL,
            freight_value REAL,
            PRIMARY KEY (order_id, order_item_id),
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            order_id TEXT,
            payment_sequential INTEGER,
            payment_type TEXT,
            payment_installments INTEGER,
            payment_value REAL,
            PRIMARY KEY (order_id, payment_sequential),
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            product_category_name TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sellers (
            seller_id TEXT PRIMARY KEY,
            seller_zip_code_prefix INTEGER,
            seller_city TEXT,
            seller_state TEXT
        );
    """)

    conn.commit()

def load_csvs_into_tables(conn: sqlite3.Connection):
    """Load CSV files into already-created tables."""
    try:
        # customers
        customers_path = DATA_DIR / "customers.csv"
        if customers_path.exists():
            df = pd.read_csv(customers_path)
            df.to_sql("customers", conn, if_exists="append", index=False)
            print(f"Loaded {len(df)} rows into customers")

        # orders
        orders_path = DATA_DIR / "orders.csv"
        if orders_path.exists():
            df = pd.read_csv(orders_path)
            df.to_sql("orders", conn, if_exists="append", index=False)
            print(f"Loaded {len(df)} rows into orders")

        # order_items
        items_path = DATA_DIR / "order_items.csv"
        if items_path.exists():
            df = pd.read_csv(items_path)
            df.to_sql("order_items", conn, if_exists="append", index=False)
            print(f"Loaded {len(df)} rows into order_items")

        # payments
        payments_path = DATA_DIR / "payments.csv"
        if payments_path.exists():
            df = pd.read_csv(payments_path)
            df.to_sql("payments", conn, if_exists="append", index=False)
            print(f"Loaded {len(df)} rows into payments")

        # products
        products_path = DATA_DIR / "products.csv"
        if products_path.exists():
            df = pd.read_csv(products_path)
            df.to_sql("products", conn, if_exists="append", index=False)
            print(f"Loaded {len(df)} rows into products")

        # sellers
        sellers_path = DATA_DIR / "sellers.csv"
        if sellers_path.exists():
            df = pd.read_csv(sellers_path)
            df.to_sql("sellers", conn, if_exists="append", index=False)
            print(f"Loaded {len(df)} rows into sellers")

        conn.commit()
    except Exception as e:
        print(f"Error loading CSV: {e}")
        conn.rollback()

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = create_connection()
    create_tables(conn)
    load_csvs_into_tables(conn)
    conn.close()
    print("Ingestion completed in", DB_PATH)

if __name__ == "__main__":
    main()

