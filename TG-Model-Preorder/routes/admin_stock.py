from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
)

from database import get_db
from config import products

from services.stock_service import (
    set_stock
)


admin_stock_bp = Blueprint(
    "admin_stock",
    __name__
)


# =========================================================
# QUẢN LÝ TỒN KHO
# =========================================================

@admin_stock_bp.route(
    "/admin/stock",
    methods=["GET", "POST"]
)
def admin_stock():

    conn = get_db()
    cursor = conn.cursor()


    try:

        # =================================================
        # CẬP NHẬT TỒN KHO
        # =================================================

        if request.method == "POST":

            try:

                product_id = int(
                    request.form.get(
                        "product_id"
                    )
                )


                stock = int(
                    request.form.get(
                        "stock",
                        0
                    )
                )

            except (TypeError, ValueError):

                return (
                    "Dữ liệu tồn kho không hợp lệ",
                    400
                )


            if stock < 0:

                stock = 0


            # =============================================
            # KIỂM TRA PRODUCT CÓ TỒN TẠI
            # =============================================

            product_exists = any(
                p["id"] == product_id
                for p in products
            )


            if not product_exists:

                return (
                    "Không tìm thấy sản phẩm",
                    404
                )


            # =============================================
            # CẬP NHẬT
            # =============================================

            set_stock(
                cursor,
                product_id,
                stock
            )


            conn.commit()


            return redirect(
                url_for(
                    "admin_stock.admin_stock"
                )
            )


        # =================================================
        # GET - LẤY DANH SÁCH TỒN KHO
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


        stock_map = {

            row[0]: row[1]

            for row in stock_rows
        }


        # =================================================
        # GHÉP CONFIG + DATABASE
        # =================================================

        product_list = []


        for product in products:

            item = product.copy()


            item["stock"] = (
                stock_map.get(
                    product["id"],
                    0
                )
            )


            product_list.append(
                item
            )


        # =================================================
        # RENDER
        # =================================================

        return render_template(
            "admin_stock.html",
            products=product_list
        )


    except Exception:

        conn.rollback()

        raise


    finally:

        cursor.close()

        conn.close()