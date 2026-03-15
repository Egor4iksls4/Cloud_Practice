import os
import random
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "shop"),
    "user": os.getenv("POSTGRES_USER", "admin"),
    "password": os.getenv("POSTGRES_PASSWORD", "secret"),
}

CUSTOMERS_COUNT = 100_000
PRODUCTS_COUNT = 10_000
ORDERS_COUNT = 500_000
BATCH_SIZE = 5_000

FIRST_NAMES = [
    "Ivan", "Petr", "Maria", "Anna", "Alexey", "Dmitry", "Olga", "Sergey",
    "Nikita", "Elena", "Andrey", "Sofia", "Maksim", "Viktoria", "Denis"
]

LAST_NAMES = [
    "Ivanov", "Petrov", "Sidorov", "Smirnov", "Kuznetsov", "Popov",
    "Volkov", "Fedorov", "Morozov", "Lebedev", "Soloviev"
]

PRODUCT_NAMES = [
    "Laptop", "Mouse", "Keyboard", "Monitor", "Headphones", "Printer",
    "USB Cable", "Desk Lamp", "Router", "SSD", "Webcam", "Microphone",
    "Tablet", "Smartphone", "Power Bank", "Charger", "Camera"
]

CATEGORIES = [
    "Electronics", "Accessories", "Office", "Gaming", "Networking"
]

STATUSES = ["pending", "completed", "shipped", "cancelled"]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_email(i: int):
    return f"user{i}@example.com"


def random_timestamp():
    base = datetime.now() - timedelta(days=365)
    delta = timedelta(
        days=random.randint(0, 365),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return base + delta


def maybe_deleted(ts):
    if random.random() < 0.03:
        return ts + timedelta(days=random.randint(1, 30))
    return None


def generate_customers(start_id: int, count: int):
    data = []
    for i in range(start_id, start_id + count):
        created_at = random_timestamp()
        deleted_at = maybe_deleted(created_at)
        data.append((
            random_name(),
            random_email(i),
            created_at,
            deleted_at,
        ))
    return data


def generate_products(start_id: int, count: int):
    data = []
    for i in range(start_id, start_id + count):
        created_at = random_timestamp()
        updated_at = created_at + timedelta(days=random.randint(0, 30))
        deleted_at = maybe_deleted(updated_at)
        data.append((
            f"{random.choice(PRODUCT_NAMES)} {i}",
            random.choice(CATEGORIES),
            round(random.uniform(500, 150000), 2),
            created_at,
            updated_at,
            deleted_at,
        ))
    return data


def generate_orders(customers_max_id: int, count: int):
    data = []
    for _ in range(count):
        created_at = random_timestamp()
        updated_at = created_at + timedelta(days=random.randint(0, 30))
        deleted_at = maybe_deleted(updated_at)
        amount = round(random.uniform(500, 150000), 2)

        data.append((
            random.randint(1, customers_max_id),
            random.choice(STATUSES),
            amount,
            created_at,
            updated_at,
            deleted_at,
        ))
    return data


def generate_order_products(order_start_id: int, order_count: int, products_max_id: int):
    data = []

    for order_id in range(order_start_id, order_start_id + order_count):
        products_in_order = random.randint(1, 5)
        product_ids = random.sample(range(1, products_max_id + 1), products_in_order)

        for product_id in product_ids:
            data.append((
                order_id,
                product_id,
                random.randint(1, 3),
                random_timestamp(),
            ))

    return data


def insert_customers(conn):
    inserted = 0
    current_start = 1

    while inserted < CUSTOMERS_COUNT:
        batch_count = min(BATCH_SIZE, CUSTOMERS_COUNT - inserted)
        batch = generate_customers(current_start, batch_count)

        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO customers (name, email, created_at, deleted_at)
                VALUES %s
                """,
                batch,
                page_size=BATCH_SIZE
            )
        conn.commit()

        inserted += batch_count
        current_start += batch_count
        print(f"Customers inserted: {inserted}/{CUSTOMERS_COUNT}")


def insert_products(conn):
    inserted = 0
    current_start = 1

    while inserted < PRODUCTS_COUNT:
        batch_count = min(BATCH_SIZE, PRODUCTS_COUNT - inserted)
        batch = generate_products(current_start, batch_count)

        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO products (name, category, price, created_at, updated_at, deleted_at)
                VALUES %s
                """,
                batch,
                page_size=BATCH_SIZE
            )
        conn.commit()

        inserted += batch_count
        current_start += batch_count
        print(f"Products inserted: {inserted}/{PRODUCTS_COUNT}")


def insert_orders(conn):
    inserted = 0
    current_start = 1

    while inserted < ORDERS_COUNT:
        batch_count = min(BATCH_SIZE, ORDERS_COUNT - inserted)
        batch = generate_orders(CUSTOMERS_COUNT, batch_count)

        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO orders (customer_id, status, amount, created_at, updated_at, deleted_at)
                VALUES %s
                """,
                batch,
                page_size=BATCH_SIZE
            )
        conn.commit()

        inserted += batch_count
        current_start += batch_count
        print(f"Orders inserted: {inserted}/{ORDERS_COUNT}")


def insert_order_products(conn):
    inserted_orders = 0
    current_order_id = 1

    while inserted_orders < ORDERS_COUNT:
        batch_count = min(BATCH_SIZE, ORDERS_COUNT - inserted_orders)
        batch = generate_order_products(current_order_id, batch_count, PRODUCTS_COUNT)

        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO order_products (order_id, product_id, quantity, created_at)
                VALUES %s
                """,
                batch,
                page_size=10_000
            )
        conn.commit()

        inserted_orders += batch_count
        current_order_id += batch_count
        print(f"Order-products generated for orders: {inserted_orders}/{ORDERS_COUNT}")


def main():
    conn = psycopg2.connect(**POSTGRES_CONFIG)

    try:
        print("Start generating customers...")
        insert_customers(conn)

        print("Start generating products...")
        insert_products(conn)

        print("Start generating orders...")
        insert_orders(conn)

        print("Start generating order_products...")
        insert_order_products(conn)

        print("Done. Test data inserted successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()