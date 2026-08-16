# =========================================================
# LẤY TẤT CẢ SẢN PHẨM
# =========================================================

def get_all_products(
    cursor,
    active_only=False
):

    sql = """
    SELECT
        p.id,
        p.name,
        p.brand,
        p.price,
        p.deposit,
        p.eta,
        p.image_url,
        p.product_type,
        p.active,

        COALESCE(
            ps.stock,
            0
        ) AS stock

    FROM products p

    LEFT JOIN product_stock ps
        ON ps.product_id = p.id
    """


    if active_only:

        sql += """
        WHERE p.active=TRUE
        """


    sql += """
    ORDER BY p.id ASC
    """


    cursor.execute(
        sql
    )


    return cursor.fetchall()


# =========================================================
# LẤY 1 SẢN PHẨM
# =========================================================

def get_product(
    cursor,
    product_id
):

    cursor.execute(
        """
        SELECT
            p.id,
            p.name,
            p.brand,
            p.price,
            p.deposit,
            p.eta,
            p.image_url,
            p.product_type,
            p.active,

            COALESCE(
                ps.stock,
                0
            ) AS stock

        FROM products p

        LEFT JOIN product_stock ps
            ON ps.product_id = p.id

        WHERE p.id=%s

        LIMIT 1
        """,
        (
            product_id,
        )
    )


    return cursor.fetchone()
