import sqlite3

conn = sqlite3.connect("cargo.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
name TEXT,
phone TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders(
id INTEGER PRIMARY KEY AUTOINCREMENT,
track TEXT,
user_id INTEGER,
from_city TEXT,
to_city TEXT,
weight REAL,
description TEXT,
status TEXT
)
""")

conn.commit()