from flask import Blueprint, request

from database import get_db

from services.order_service import (
    normalize_expires_at,
    is_order_expired,
    expires_to_timestamp,
    mark_order_expired
)


pending_order_bp = Blueprint(
    "pending_order",
    __name__
)


# =========================================================
# API KIỂM TRA ĐƠN CHƯA THANH TOÁN
# =========================================================

@pending_order_bp.route(
    "/api/pending-order"
)
def pending_order():

    order_token = request.cookies.get(
        "order_token"
    )


    # =====================================================
    # KHÔNG CÓ COOKIE
    # =====================================================

    if not order_token:

        return {
            "has_order": False
        }


    conn = get_db()
    cursor = conn.cursor()


    try:

        # =================================================
        # TÌM ĐƠN CHƯA THANH TOÁN GẦN NHẤT
        # =================================================

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


        # =================================================
        # KHÔNG CÓ ĐƠN
        # =================================================

        if order is None:

            return {
                "has_order": False
            }


        order_code = order[0]
        product_name = order[1]
        quantity = order[2]
        deposit = order[3]
        payment_url = order[4]

        expires_at = normalize_expires_at(
            order[5]
        )


        # =================================================
        # KHÔNG CÓ THỜI GIAN HẾT HẠN
        # =================================================

        if expires_at is None:

            return {
                "has_order": False
            }


        # =================================================
        # ĐÃ HẾT HẠN
        # =================================================

        if is_order_expired(
            expires_at
        ):

            mark_order_expired(
                cursor,
                conn,
                order_code
            )


            return {
                "has_order": False
            }


        # =================================================
        # CHƯA CÓ LINK PAYOS
        # =================================================

        if not payment_url:

            return {
                "has_order": False
            }


        # =================================================
        # UNIX TIMESTAMP
        # =================================================

        expires_timestamp = (
            expires_to_timestamp(
                expires_at
            )
        )


        # =================================================
        # TRẢ DỮ LIỆU CHO INDEX.HTML
        # =================================================

        return {

            "has_order": True,

            "order_code":
                order_code,

            "product_name":
                product_name,

            "quantity":
                quantity,

            "deposit":
                deposit,

            "payment_url":
                payment_url,

            "expires_at":
                expires_timestamp
        }


    finally:

        cursor.close()
        conn.close()