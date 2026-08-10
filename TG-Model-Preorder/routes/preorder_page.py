from flask import (
    Blueprint,
    request,
    render_template
)

from psycopg2.extras import RealDictCursor

from database import get_db

from services.order_service import (
    normalize_expires_at,
    is_order_expired,
    mark_order_expired
)


preorder_page_bp = Blueprint(
    "preorder_page",
    __name__
)


# =========================================================
# TRANG PRE-ORDER
# =========================================================

@preorder_page_bp.route(
    "/preorder/<int:product_id>"
)
def preorder(product_id):

    # =====================================================
    # DATABASE
    # =====================================================

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        # =================================================
        # TÌM SẢN PHẨM TRỰC TIẾP TỪ DATABASE
        # + ẢNH
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
                p.image_url,
                p.active,

                COALESCE(
                    ps.stock,
                    0
                ) AS stock

            FROM products p

            LEFT JOIN product_stock ps
                ON ps.product_id = p.id

            WHERE p.id=%s
            AND p.active=TRUE

            LIMIT 1
            """,
            (
                product_id,
            )
        )


        product = cursor.fetchone()


        # =================================================
        # KHÔNG TÌM THẤY SẢN PHẨM
        # =================================================

        if product is None:

            return (
                "Không tìm thấy sản phẩm",
                404
            )


        # =================================================
        # KIỂM TRA TỒN KHO
        # =================================================

        if product["stock"] <= 0:

            return (
                "Sản phẩm hiện đã hết hàng",
                400
            )


        # =================================================
        # KIỂM TRA ĐƠN CŨ THEO COOKIE
        # =================================================

        order_token = request.cookies.get(
            "order_token"
        )


        existing_order = None


        if order_token:

            cursor.execute(
                """
                SELECT
                    order_code,
                    product_name,
                    quantity,
                    deposit,
                    payment_url,
                    expires_at,
                    status

                FROM orders

                WHERE order_token=%s
                AND status=%s

                ORDER BY id DESC

                LIMIT 1
                """,
                (
                    order_token,
                    "Chưa thanh toán"
                )
            )


            order = cursor.fetchone()


            if order:

                expires_at = (
                    normalize_expires_at(
                        order["expires_at"]
                    )
                )


                # =========================================
                # ĐƠN ĐÃ HẾT HẠN
                # =========================================

                if is_order_expired(
                    expires_at
                ):

                    mark_order_expired(
                        cursor,
                        conn,
                        order["order_code"]
                    )


                # =========================================
                # ĐƠN VẪN CÒN HẠN
                # =========================================

                else:

                    existing_order = order


        # =================================================
        # HIỂN THỊ FORM
        # =================================================

        return render_template(
            "preorder.html",
            product=product,
            existing_order=existing_order
        )


    finally:

        cursor.close()

        conn.close()
