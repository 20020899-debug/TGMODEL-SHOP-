from database import get_db


conn = get_db()

cursor = conn.cursor()


# ==========================================
# Tạo bảng orders nếu chưa tồn tại
# ==========================================

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


# ==========================================
# Thêm expires_at nếu bảng cũ chưa có
# ==========================================

cursor.execute("""
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP
""")


# ==========================================
# Thêm payment_url nếu bảng cũ chưa có
# ==========================================

cursor.execute("""
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS payment_url TEXT
""")


# ==========================================
# Thêm order_token nếu bảng cũ chưa có
# ==========================================

cursor.execute("""
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS order_token TEXT
""")


conn.commit()


cursor.close()
conn.close()


print("PostgreSQL OK")
