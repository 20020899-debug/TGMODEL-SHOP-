from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from psycopg2.extras import RealDictCursor

from database import get_db

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

    # =====================================================
    # KIỂM TRA ĐĂNG NHẬP ADMIN
    # =====================================================

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


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


            # =============================================
            # KHÔNG CHO STOCK ÂM
            # =============================================

            if stock < 0:

                stock = 0


            # =============================================
            # KIỂM TRA PRODUCT CÓ TỒN TẠI
            # =============================================

            cursor.execute(
                """
                SELECT id

                FROM products

                WHERE id=%s

                LIMIT 1
                """,
                (
                    product_id,
                )
            )


            product = cursor.fetchone()


            if product is None:

                return (
                    "Không tìm thấy sản phẩm",
                    404
                )


            # =============================================
            # CẬP NHẬT TỒN KHO
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
        # GET - LẤY SẢN PHẨM + TỒN KHO
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

            ORDER BY
                p.active DESC,
                p.id ASC
            """
        )


        product_list = cursor.fetchall()


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
