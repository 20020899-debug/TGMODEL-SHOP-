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
        # HIỂN THỊ TRANG CHỦ
        # =================================================

        return render_template(
            "index.html",
            products=products
        )


    finally:

        cursor.close()

        conn.close()
