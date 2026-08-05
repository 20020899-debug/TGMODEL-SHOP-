import sqlite3


conn = sqlite3.connect("orders.db")

cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS products(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    brand TEXT,

    name TEXT,

    price INTEGER,

    deposit INTEGER,

    eta TEXT,

    image TEXT,

    status TEXT

)
""")


conn.commit()

conn.close()


print("Đã tạo bảng products")