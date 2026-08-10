from flask import (
    Blueprint,
    render_template
)

from psycopg2.extras import RealDictCursor

from database import get_db


home_bp = Blueprint(
    "home",
    __name__
)


# =========================================================
# TRANG CHỦ
# =========================================================

@home_bp.route("/")
def home():

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        # =================================================
        # LẤY SẢN PHẨM ĐANG HOẠT ĐỘNG
        # + TỒN KHO
        # =================================================

        cursor.execute(
            """
            SELECT
                p.id,
                p.name,
                p.brand,
                p.price,
                p.deposit,
                p.eta,
                p.active,

                COALESCE(
                    ps.stock,
                    0
                ) AS stock

            FROM products p

            LEFT JOIN product_stock ps
                ON ps.product_id = p.id

            WHERE p.active = TRUE

            ORDER BY p.id ASC
            """
        )


        products = cursor.fetchall()


        # =================================================
        # TRANG CHỦ
        # =================================================

        return render_template(
            "index.html",
            products=products
        )


    finally:

        cursor.close()

        conn.close()


# =========================================================
# TRANG PRE-ORDER SẢN PHẨM
# =========================================================

@home_bp.route(
    "/preorder/<int:id>"
)
def preorder(id):

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        # =================================================
        # TÌM SẢN PHẨM THEO ID
        # =================================================

        cursor.execute(
            """
            SELECT
                p.id,
                p.name,
                p.brand,
                p.price,
                p.deposit,
                p.eta,
                p.active,

                COALESCE(
                    ps.stock,
                    0
                ) AS stock

            FROM products p

            LEFT JOIN product_stock ps
                ON ps.product_id = p.id

            WHERE p.id = %s
            AND p.active = TRUE

            LIMIT 1
            """,
            (
                id,
            )
        )


        product = cursor.fetchone()


        # =================================================
        # KHÔNG TÌM THẤY
        # =================================================

        if product is None:

            return (
                "Không tìm thấy sản phẩm",
                404
            )


        # =================================================
        # TRANG ĐẶT HÀNG
        # =================================================

        return render_template(
            "preorder.html",
            product=product
        )


    finally:

        cursor.close()

        conn.close()
