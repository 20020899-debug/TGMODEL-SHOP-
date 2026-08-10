from flask import (
    Blueprint,
    render_template
)

from config import products
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
    cursor = conn.cursor()


    try:

        # =================================================
        # LẤY TỒN KHO
        # =================================================

        cursor.execute(
            """
            SELECT
                product_id,
                stock

            FROM product_stock
            """
        )


        stock_rows = cursor.fetchall()


        # =================================================
        # CHUYỂN THÀNH DICTIONARY
        #
        # Ví dụ:
        #
        # {
        #     1: 5,
        #     2: 10
        # }
        # =================================================

        stock_map = {

            row[0]: row[1]

            for row in stock_rows
        }


        # =================================================
        # GẮN TỒN KHO VÀO SẢN PHẨM
        #
        # Không sửa trực tiếp products trong config.py
        # =================================================

        products_with_stock = []


        for product in products:

            item = product.copy()


            item["stock"] = (
                stock_map.get(
                    product["id"],
                    0
                )
            )


            products_with_stock.append(
                item
            )


        # =================================================
        # RENDER TRANG CHỦ
        # =================================================

        return render_template(
            "index.html",
            products=products_with_stock
        )


    finally:

        cursor.close()

        conn.close()
