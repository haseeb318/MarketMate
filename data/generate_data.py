import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "marketmate.db"
random.seed(42)

PRODUCTS = [
    ("Blue Kurta", "Fashion", 2999, 1700, 80),
    ("White Shalwar", "Fashion", 1999, 1100, 15),
    ("Black Waistcoat", "Fashion", 3499, 2100, 45),
    ("Gardening Set", "Home & Garden", 2499, 1500, 300),
    ("LED Fairy Lights", "Home", 1299, 650, 120),
    ("Kitchen Organizer", "Home", 1799, 900, 75),
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS orders")
cur.execute("DROP TABLE IF EXISTS products")
cur.execute("DROP TABLE IF EXISTS events")

cur.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    category TEXT,
    price REAL,
    cost REAL,
    stock INTEGER
)
""")

cur.execute("""
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    order_date TEXT,
    product_id INTEGER,
    quantity INTEGER,
    revenue REAL,
    profit REAL
)
""")

cur.execute("""
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_date TEXT,
    name TEXT,
    description TEXT
)
""")

for product in PRODUCTS:
    cur.execute(
        "INSERT INTO products (name, category, price, cost, stock) VALUES (?, ?, ?, ?, ?)",
        product
    )

today = date.today()

for days_ago in range(60, 0, -1):
    order_date = today - timedelta(days=days_ago)

    for product_id, product in enumerate(PRODUCTS, 1):
        name, category, price, cost, stock = product

        if name == "Blue Kurta":
            quantity = random.randint(2, 5) + (60 - days_ago) // 10
        elif name == "Gardening Set":
            quantity = random.randint(0, 1)
        elif name == "White Shalwar":
            quantity = random.randint(0, 2)
        else:
            quantity = random.randint(0, 4)

        if quantity == 0:
            continue

        revenue = quantity * price
        profit = quantity * (price - cost)

        cur.execute(
            """INSERT INTO orders
            (order_date, product_id, quantity, revenue, profit)
            VALUES (?, ?, ?, ?, ?)""",
            (order_date.isoformat(), product_id, quantity, revenue, profit)
        )

events = [
    (today + timedelta(days=10), "Eid Campaign",
     "Eid shopping promotion opportunity."),
    (today + timedelta(days=18), "Weekend Sale",
     "Weekend promotional campaign opportunity."),
    (today + timedelta(days=30), "Independence Day",
     "Pakistan Independence Day marketing opportunity."),
]

for event_date, name, description in events:
    cur.execute(
        "INSERT INTO events (event_date, name, description) VALUES (?, ?, ?)",
        (event_date.isoformat(), name, description)
    )

conn.commit()
conn.close()

print("MarketMate database created successfully.")
print("Products: 6")
print("Orders: generated for 60 days")
print("Events: 3")
