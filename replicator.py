import os
from datetime import datetime, timezone
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "shop"),
    "user": os.getenv("POSTGRES_USER", "admin"),
    "password": os.getenv("POSTGRES_PASSWORD", "secret"),
}

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB = os.getenv("MONGO_DB", "shop_replica")
LAST_SYNC_FILE = os.getenv("LAST_SYNC_FILE", "state/last_sync.txt")


def ensure_last_sync_file():
    directory = os.path.dirname(LAST_SYNC_FILE)
    if directory:
        os.makedirs(directory, exist_ok=True)

    if not os.path.exists(LAST_SYNC_FILE) or os.path.getsize(LAST_SYNC_FILE) == 0:
        with open(LAST_SYNC_FILE, "w", encoding="utf-8") as f:
            f.write("1970-01-01T00:00:00+00:00")


def read_last_sync():
    ensure_last_sync_file()
    with open(LAST_SYNC_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return datetime.fromisoformat(content)


def save_last_sync(ts: datetime):
    with open(LAST_SYNC_FILE, "w", encoding="utf-8") as f:
        f.write(ts.astimezone(timezone.utc).isoformat())


def normalize_value(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def build_customer_document(cur, customer_id):
    cur.execute("""
        SELECT id, name, email, created_at, deleted_at
        FROM customers
        WHERE id = %s
    """, (customer_id,))
    customer = cur.fetchone()

    if not customer:
        return None

    cur.execute("""
        SELECT
            o.id AS order_id,
            o.status,
            o.amount,
            o.created_at,
            o.updated_at,
            o.deleted_at
        FROM orders o
        WHERE o.customer_id = %s
        ORDER BY o.id
    """, (customer_id,))
    orders = cur.fetchall()

    order_docs = []

    for order in orders:
        order_id = order["order_id"]

        cur.execute("""
            SELECT
                p.id AS product_id,
                p.name,
                p.category,
                p.price,
                p.created_at,
                p.updated_at,
                p.deleted_at,
                op.quantity
            FROM order_products op
            JOIN products p ON p.id = op.product_id
            WHERE op.order_id = %s
            ORDER BY p.id
        """, (order_id,))
        products = cur.fetchall()

        product_docs = []
        for product in products:
            product_docs.append({
                "product_id": product["product_id"],
                "name": product["name"],
                "category": product["category"],
                "price": normalize_value(product["price"]),
                "quantity": product["quantity"],
                "created_at": product["created_at"],
                "updated_at": product["updated_at"],
                "deleted_at": product["deleted_at"],
            })

        order_docs.append({
            "order_id": order["order_id"],
            "status": order["status"],
            "amount": normalize_value(order["amount"]),
            "created_at": order["created_at"],
            "updated_at": order["updated_at"],
            "deleted_at": order["deleted_at"],
            "products": product_docs,
        })

    return {
        "_id": customer["id"],
        "name": customer["name"],
        "email": customer["email"],
        "created_at": customer["created_at"],
        "deleted_at": customer["deleted_at"],
        "orders": order_docs,
        "synced_at": datetime.now(timezone.utc),
    }


def get_changed_customer_ids(cur, last_sync):
    changed_ids = set()

    cur.execute("""
        SELECT id
        FROM customers
        WHERE created_at > %s OR deleted_at > %s
    """, (last_sync, last_sync))
    changed_ids.update(row["id"] for row in cur.fetchall())

    cur.execute("""
        SELECT DISTINCT customer_id AS id
        FROM orders
        WHERE updated_at > %s OR deleted_at > %s
    """, (last_sync, last_sync))
    changed_ids.update(row["id"] for row in cur.fetchall())

    cur.execute("""
        SELECT DISTINCT o.customer_id AS id
        FROM order_products op
        JOIN orders o ON o.id = op.order_id
        JOIN products p ON p.id = op.product_id
        WHERE p.updated_at > %s OR p.deleted_at > %s
    """, (last_sync, last_sync))
    changed_ids.update(row["id"] for row in cur.fetchall())

    return changed_ids


def replicate():
    last_sync = read_last_sync()
    now = datetime.now(timezone.utc)

    pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
    mongo_client = MongoClient(MONGO_HOST, MONGO_PORT)
    mongo_db = mongo_client[MONGO_DB]
    collection = mongo_db.customers

    try:
        with pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            changed_customer_ids = get_changed_customer_ids(cur, last_sync)

            for customer_id in changed_customer_ids:
                customer_doc = build_customer_document(cur, customer_id)
                if customer_doc is not None:
                    collection.replace_one(
                        {"_id": customer_doc["_id"]},
                        customer_doc,
                        upsert=True
                    )

        save_last_sync(now)
        print(f"Replication completed at {now.isoformat()}")
        print(f"Customers synchronized: {len(changed_customer_ids)}")

    finally:
        pg_conn.close()
        mongo_client.close()


if __name__ == "__main__":
    replicate()