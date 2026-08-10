from flask import Blueprint, request, render_template

from database import get_db
from config import products

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
    # TÌM SẢN PHẨM
    # =====================================================

    product = next(
        (
            p
            for p in products
            if p["id"] == product_id
        ),
        None
    )


    if product is None:

        return (
            "Không tìm thấy sản phẩm",
            404
        )


    # =====================================================
    # KIỂM TRA ĐƠN CŨ THEO COOKIE
    # =====================================================

    order_token = request.cookies.get(
        "order_token"
    )


    existing_order = None


    if order_token:

        conn = get_db()
        cursor = conn.cursor()


        try:

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

                expires_at = normalize_expires_at(
                    order[5]
                )


                # =========================================
                # ĐÃ HẾT HẠN
                # =========================================

                if is_order_expired(
                    expires_at
                ):

                    mark_order_expired(
                        cursor,
                        conn,
                        order[0]
                    )


                # =========================================
                # CÒN HẠN
                # =========================================

                else:

                    existing_order = order


        finally:

            cursor.close()
            conn.close()


    # =====================================================
    # HIỂN THỊ FORM
    # =====================================================

    return render_template(
        "preorder.html",
        product=product,
        existing_order=existing_order
    )