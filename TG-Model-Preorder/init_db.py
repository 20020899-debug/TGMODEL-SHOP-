from database import get_db


conn = get_db()

cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (

    id SERIAL PRIMARY KEY,

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

    status TEXT,

    created_at TEXT,
    expires_at TIMESTAMP,

    payment_url TEXT,
    order_token TEXT

)
""")


conn.commit()

cursor.close()
conn.close()


print("PostgreSQL OK")
