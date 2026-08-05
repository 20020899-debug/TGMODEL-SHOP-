import sqlite3

conn = sqlite3.connect("orders.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    order_code TEXT,

    fullname TEXT,

    phone TEXT,

    contact TEXT,

    province TEXT,

    district TEXT,

    ward TEXT,

    address_detail TEXT,

    quantity INTEGER,

    note TEXT,

    product_name TEXT,

    product_brand TEXT,

    price INTEGER,

    deposit INTEGER,

    status TEXT

)
""")

conn.commit()
conn.close()

print("Database đã tạo.")