from database import get_db


# =========================================================
# KẾT NỐI DATABASE
# =========================================================

conn = get_db()

cursor = conn.cursor()


try:

    # =====================================================
    # TẠO BẢNG ORDERS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders
        (
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

            payment_type TEXT,
            status TEXT,

            created_at TEXT,
            expires_at TIMESTAMP,

            payment_url TEXT,
            order_token TEXT,

            product_id INTEGER,

            stock_reserved BOOLEAN
                NOT NULL
                DEFAULT FALSE
        )
        """
    )


    # =====================================================
    # BỔ SUNG CỘT CHO DATABASE ORDERS CŨ
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            expires_at TIMESTAMP
        """
    )


    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            payment_type TEXT
        """
    )


    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            payment_url TEXT
        """
    )


    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            order_token TEXT
        """
    )


    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            product_id INTEGER
        """
    )


    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            stock_reserved BOOLEAN
            NOT NULL
            DEFAULT FALSE
        """
    )


    # =====================================================
    # TẠO BẢNG PRODUCTS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products
        (
            id SERIAL PRIMARY KEY,

            name TEXT
                NOT NULL,

            brand TEXT,

            price INTEGER
                NOT NULL
                DEFAULT 0,

            deposit INTEGER
                NOT NULL
                DEFAULT 0,

            eta TEXT,

            image_url TEXT,

            active BOOLEAN
                NOT NULL
                DEFAULT TRUE
        )
        """
    )


    # =====================================================
    # BỔ SUNG CỘT PRODUCTS CHO DATABASE CŨ
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE products

        ADD COLUMN IF NOT EXISTS
            name TEXT
        """
    )


    cursor.execute(
        """
        ALTER TABLE products

        ADD COLUMN IF NOT EXISTS
            brand TEXT
        """
    )


    cursor.execute(
        """
        ALTER TABLE products

        ADD COLUMN IF NOT EXISTS
            price INTEGER
            NOT NULL
            DEFAULT 0
        """
    )


    cursor.execute(
        """
        ALTER TABLE products

        ADD COLUMN IF NOT EXISTS
            deposit INTEGER
            NOT NULL
            DEFAULT 0
        """
    )


    cursor.execute(
        """
        ALTER TABLE products

        ADD COLUMN IF NOT EXISTS
            eta TEXT
        """
    )


    # =====================================================
    # IMAGE URL
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE products

        ADD COLUMN IF NOT EXISTS
            image_url TEXT
        """
    )


    cursor.execute(
        """
        ALTER TABLE products

        ADD COLUMN IF NOT EXISTS
            active BOOLEAN
            NOT NULL
            DEFAULT TRUE
        """
    )


    # =====================================================
    # TẠO BẢNG TỒN KHO
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS product_stock
        (
            product_id INTEGER PRIMARY KEY,

            stock INTEGER
                NOT NULL
                DEFAULT 0,

            CONSTRAINT product_stock_not_negative
                CHECK (stock >= 0)
        )
        """
    )


    # =====================================================
    # BỔ SUNG STOCK CHO DATABASE CŨ
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE product_stock

        ADD COLUMN IF NOT EXISTS
            stock INTEGER
            NOT NULL
            DEFAULT 0
        """
    )


    # =====================================================
    # ĐẢM BẢO MỌI PRODUCT ĐỀU CÓ DÒNG STOCK
    # =====================================================

    cursor.execute(
        """
        INSERT INTO product_stock
        (
            product_id,
            stock
        )

        SELECT
            p.id,
            0

        FROM products p

        LEFT JOIN product_stock ps
            ON ps.product_id = p.id

        WHERE ps.product_id IS NULL
        """
    )


    # =====================================================
    # ĐỒNG BỘ SEQUENCE PRODUCTS.ID
    # =====================================================

    cursor.execute(
        """
        SELECT setval(
            pg_get_serial_sequence(
                'products',
                'id'
            ),

            GREATEST(
                COALESCE(
                    (
                        SELECT MAX(id)
                        FROM products
                    ),
                    1
                ),
                1
            ),

            TRUE
        )
        """
    )


    # =====================================================
    # INDEX ORDERS - PRODUCT ID
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_orders_product_id

        ON orders(product_id)
        """
    )


    # =====================================================
    # INDEX ORDERS - ORDER TOKEN
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_orders_order_token

        ON orders(order_token)
        """
    )


    # =====================================================
    # INDEX ORDERS - STATUS
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_orders_status

        ON orders(status)
        """
    )


    # =====================================================
    # INDEX PRODUCTS - ACTIVE
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_products_active

        ON products(active)
        """
    )


    # =====================================================
    # INDEX PRODUCTS - NAME
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_products_name

        ON products(name)
        """
    )


    # =====================================================
    # COMMIT
    # =====================================================

    conn.commit()


    print(
        "======================================"
    )

    print(
        "PostgreSQL OK"
    )

    print(
        "orders: OK"
    )

    print(
        "products: OK"
    )

    print(
        "product_stock: OK"
    )

    print(
        "payment_type: OK"
    )

    print(
        "product_id: OK"
    )

    print(
        "stock_reserved: OK"
    )

    print(
        "image_url: OK"
    )

    print(
        "Product ID sequence: OK"
    )

    print(
        "Không còn phụ thuộc config.py"
    )

    print(
        "======================================"
    )


# =========================================================
# LỖI
# =========================================================

except Exception as error:

    conn.rollback()


    print(
        "======================================"
    )

    print(
        "LỖI KHỞI TẠO DATABASE:"
    )

    print(
        error
    )

    print(
        "======================================"
    )


    raise


# =========================================================
# ĐÓNG DATABASE
# =========================================================

finally:

    cursor.close()

    conn.close()
