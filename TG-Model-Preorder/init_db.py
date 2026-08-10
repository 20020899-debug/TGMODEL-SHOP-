from database import get_db
from config import products


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

            status TEXT,
            payment_type TEXT,

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
    # CỘT EXPIRES_AT
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            expires_at TIMESTAMP
        """
    )
    # =====================================================
    # CHUYỂN KHOẢN FULL
    # =====================================================
    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            payment_type TEXT
        """
    )



    # =====================================================
    # CỘT PAYMENT_URL
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            payment_url TEXT
        """
    )


    # =====================================================
    # CỘT ORDER_TOKEN
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            order_token TEXT
        """
    )


    # =====================================================
    # PRODUCT ID
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE orders

        ADD COLUMN IF NOT EXISTS
            product_id INTEGER
        """
    )


    # =====================================================
    # STOCK RESERVED
    # =====================================================

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
    # ĐỒNG BỘ SẢN PHẨM TỪ CONFIG.PY
    #
    # Chỉ thêm sản phẩm chưa tồn tại.
    # Không ghi đè tồn kho cũ.
    # =====================================================

    for product in products:

        product_id = product.get(
            "id"
        )


        if product_id is None:

            continue


        cursor.execute(
            """
            INSERT INTO product_stock
            (
                product_id,
                stock
            )

            VALUES
            (
                %s,
                0
            )

            ON CONFLICT (product_id)
            DO NOTHING
            """,
            (
                product_id,
            )
        )


    # =====================================================
    # INDEX PRODUCT ID
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_orders_product_id

        ON orders(product_id)
        """
    )


    # =====================================================
    # INDEX ORDER TOKEN
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_orders_order_token

        ON orders(order_token)
        """
    )


    # =====================================================
    # INDEX STATUS
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_orders_status

        ON orders(status)
        """
    )


    # =====================================================
    # LƯU DATABASE
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
        "product_id: OK"
    )

    print(
        "stock_reserved: OK"
    )

    print(
        "product_stock: OK"
    )

    print(
        "Đồng bộ sản phẩm: OK"
    )

    print(
        "======================================"
    )


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


finally:

    cursor.close()

    conn.close()
