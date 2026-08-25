from database import get_db


conn = get_db()
cursor = conn.cursor()


try:

    # =====================================================
    # ORDERS
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

            tracking_code TEXT,

            created_at TEXT,

            -- Thanh toán ban đầu / tiền cọc
            expires_at TIMESTAMP,
            payment_url TEXT,

            -- Thanh toán phần còn lại của Pre-order
            remaining_payment_url TEXT,
            remaining_expires_at TIMESTAMP,

            order_token TEXT,
            product_id INTEGER,

            stock_reserved BOOLEAN NOT NULL DEFAULT FALSE
        )
        """
    )


    # =====================================================
    # ORDERS - CỘT CHO DATABASE CŨ
    #
    # Các lệnh này đảm bảo database đã tạo từ trước cũng
    # được bổ sung các cột mới mà không làm mất dữ liệu.
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP
        """
    )

    cursor.execute(
        """
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS payment_type TEXT
        """
    )

    cursor.execute(
        """
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS payment_url TEXT
        """
    )

    cursor.execute(
        """
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS order_token TEXT
        """
    )

    cursor.execute(
        """
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS product_id INTEGER
        """
    )

    cursor.execute(
        """
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS tracking_code TEXT
        """
    )

    cursor.execute(
        """
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS stock_reserved BOOLEAN
        NOT NULL DEFAULT FALSE
        """
    )


    # =====================================================
    # THANH TOÁN PHẦN CÒN LẠI CỦA PRE-ORDER
    #
    # remaining_payment_url:
    # Link PayOS dùng để thanh toán phần tiền còn lại.
    #
    # remaining_expires_at:
    # Thời điểm link PayOS phần còn lại hết hạn.
    #
    # Lưu ý:
    # Hết hạn link này KHÔNG được hủy đơn và KHÔNG hoàn kho.
    # Khách có thể tạo link thanh toán mới.
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS remaining_payment_url TEXT
        """
    )

    cursor.execute(
        """
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS remaining_expires_at TIMESTAMP
        """
    )


    # =====================================================
    # PRODUCTS
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products
        (
            id SERIAL PRIMARY KEY,

            name TEXT NOT NULL,
            brand TEXT,

            price INTEGER NOT NULL DEFAULT 0,
            deposit INTEGER NOT NULL DEFAULT 0,

            eta TEXT,
            image_url TEXT,

            product_type TEXT NOT NULL DEFAULT 'preorder',
            active BOOLEAN NOT NULL DEFAULT TRUE
        )
        """
    )


    # =====================================================
    # PRODUCTS - CỘT CHO DATABASE CŨ
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS name TEXT
        """
    )

    cursor.execute(
        """
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS brand TEXT
        """
    )

    cursor.execute(
        """
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS price INTEGER
        NOT NULL DEFAULT 0
        """
    )

    cursor.execute(
        """
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS deposit INTEGER
        NOT NULL DEFAULT 0
        """
    )

    cursor.execute(
        """
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS eta TEXT
        """
    )

    cursor.execute(
        """
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS image_url TEXT
        """
    )


    # =====================================================
    # LOẠI SẢN PHẨM
    #
    # preorder = hàng Pre-order
    # instock  = hàng sẵn
    #
    # Sản phẩm cũ mặc định là preorder.
    # =====================================================

    cursor.execute(
        """
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS product_type TEXT
        NOT NULL DEFAULT 'preorder'
        """
    )

    cursor.execute(
        """
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS active BOOLEAN
        NOT NULL DEFAULT TRUE
        """
    )


    # =====================================================
    # TỒN KHO
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS product_stock
        (
            product_id INTEGER PRIMARY KEY,

            stock INTEGER NOT NULL DEFAULT 0,

            CONSTRAINT product_stock_not_negative
                CHECK (stock >= 0)
        )
        """
    )

    cursor.execute(
        """
        ALTER TABLE product_stock
        ADD COLUMN IF NOT EXISTS stock INTEGER
        NOT NULL DEFAULT 0
        """
    )


    # =====================================================
    # ĐẢM BẢO MỌI PRODUCT ĐỀU CÓ STOCK
    # =====================================================

    cursor.execute(
        """
        INSERT INTO product_stock (product_id, stock)

        SELECT p.id, 0

        FROM products p

        LEFT JOIN product_stock ps
            ON ps.product_id = p.id

        WHERE ps.product_id IS NULL
        """
    )


    # =====================================================
    # ĐỒNG BỘ SEQUENCE PRODUCTS.ID
    #
    # Tránh trường hợp PostgreSQL tạo ID mới bị trùng với
    # sản phẩm đã tồn tại.
    # =====================================================

    cursor.execute(
        """
        SELECT setval(
            pg_get_serial_sequence('products', 'id'),

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
    # INDEX ORDERS
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_orders_product_id
        ON orders(product_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_orders_order_token
        ON orders(order_token)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_orders_status
        ON orders(status)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_orders_tracking_code
        ON orders(tracking_code)
        """
    )


    # =====================================================
    # INDEX PRODUCTS
    # =====================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_products_active
        ON products(active)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_products_name
        ON products(name)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_products_type
        ON products(product_type)
        """
    )


    # =====================================================
    # COMMIT
    # =====================================================

    conn.commit()

    print("======================================")
    print("PostgreSQL OK")
    print("orders: OK")
    print("products: OK")
    print("product_stock: OK")
    print("payment_type: OK")
    print("tracking_code: OK")
    print("image_url: OK")
    print("product_type: OK")
    print("remaining_payment_url: OK")
    print("remaining_expires_at: OK")
    print("Product ID sequence: OK")
    print("======================================")


except Exception as error:

    conn.rollback()

    print("======================================")
    print("LỖI KHỞI TẠO DATABASE:")
    print(error)
    print("======================================")

    raise


finally:

    cursor.close()
    conn.close()
