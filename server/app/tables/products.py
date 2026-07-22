"""Products table: schema (DDL) and deterministic seed data."""

import sqlite3

SCHEMA = """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        section TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        discount REAL NOT NULL DEFAULT 0,
        price REAL NOT NULL
    )
"""

SEED = [
    ("Wireless Mouse", "electronics", "Ergonomic 2.4GHz wireless mouse", 0.0, 25.0),
    (
        "Mechanical Keyboard",
        "electronics",
        "RGB backlit mechanical keyboard",
        10.0,
        80.0,
    ),
    ("USB-C Hub", "electronics", "7-in-1 USB-C hub adapter", 0.0, 45.0),
    (
        "Noise Cancelling Headphones",
        "electronics",
        "Over-ear ANC headphones",
        15.0,
        200.0,
    ),
    (
        "The Pragmatic Programmer",
        "books",
        "Classic software craftsmanship book",
        0.0,
        40.0,
    ),
    ("Clean Code", "books", "A handbook of agile software craftsmanship", 5.0, 35.0),
    (
        "Designing Data-Intensive Applications",
        "books",
        "Data systems reference",
        0.0,
        55.0,
    ),
    ("Dark Roast Coffee", "food", "500g bag of whole beans", 0.0, 15.0),
    ("Organic Green Tea", "food", "Loose leaf green tea, 200g", 0.0, 12.0),
    ("Dark Chocolate Bar", "food", "70% cocoa, single origin", 20.0, 6.0),
    ("Cotton T-Shirt", "clothing", "Plain crew-neck cotton t-shirt", 0.0, 18.0),
    ("Wool Socks", "clothing", "Merino wool hiking socks", 0.0, 14.0),
    ("Rain Jacket", "clothing", "Lightweight waterproof jacket", 25.0, 90.0),
    ("Standing Desk", "furniture", "Electric height-adjustable desk", 10.0, 320.0),
    ("Office Chair", "furniture", "Ergonomic mesh office chair", 5.0, 180.0),
]


def seed(conn: sqlite3.Connection) -> None:
    """Insert the deterministic product catalog."""
    conn.executemany(
        "INSERT INTO products (name, section, description, discount, price) "
        "VALUES (?, ?, ?, ?, ?)",
        SEED,
    )
