from flask import (
    Blueprint,
    render_template,
    request
)

from psycopg2.extras import RealDictCursor

from database import get_db

from services.order_service import (
    normalize_expires_at,
    is_order_expired,
    mark_order_expired
)


order_tracking_bp = Blueprint(
    "order_tracking",
    __name__
)


# =========================================================
# TRANG THEO DÕI ĐƠN HÀNG
# =========================================================

@order_tracking_bp.route(
    "/order-status",
    methods=["GET", "POST"]
)
def order_status():

    # =====================================================
    # COOKIE CỦA KHÁCH
    # =====================================================

    order_token = request.cookies.get(
        "order_token"
    )


    order = None

    error = None


    # =====================================================
    # DATABASE
    # =====================================================

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        # =================================================
        # POST
        #
        # KHÁCH NHẬP:
        # - MÃ ĐƠN
        # - SỐ ĐIỆN THOẠI
        # =================================================

        if request.method == "POST":

            order_code = request.form.get(
                "order_code",
                ""
            ).strip()


            phone = request.form.get(
                "phone",
                ""
            ).strip()


            # =============================================
            # THIẾU DỮ LIỆU
            # =============================================

            if (
                not order_code
                or
                not phone
            ):

                error = (
                    "Vui lòng nhập mã đơn "
                    "và số điện thoại."
                )


            else:

                cursor.execute(
                    """
                    SELECT *

                    FROM orders

                    WHERE order_code=%s
                    AND phone=%s

                    LIMIT 1
                    """,
                    (
                        order_code,
                        phone
                    )
                )


                order = cursor.fetchone()


                if order is None:

                    error = (
                        "Không tìm thấy đơn hàng "
                        "phù hợp."
                    )


        # =================================================
        # GET
        #
        # NẾU KHÁCH ĐANG DÙNG ĐÚNG THIẾT BỊ ĐÃ ĐẶT
        # → TỰ TÌM ĐƠN THEO COOKIE
        # =================================================

        elif order_token:

            cursor.execute(
                """
                SELECT *

                FROM orders

                WHERE order_token=%s

                ORDER BY id DESC

                LIMIT 1
                """,
                (
                    order_token,
                )
            )


            order = cursor.fetchone()


        # =================================================
        # KIỂM TRA ĐƠN HẾT HẠN
        # =================================================

        if (
            order
            and
            order["status"]
            ==
            "Chưa thanh toán"
        ):

            expires_at = (
                normalize_expires_at(
                    order["expires_at"]
                )
            )


            if is_order_expired(
                expires_at
            ):

                mark_order_expired(
                    cursor,
                    conn,
                    order["order_code"]
                )


                # =========================================
                # ĐỌC LẠI ĐƠN SAU KHI UPDATE
                # =========================================

                cursor.execute(
                    """
                    SELECT *

                    FROM orders

                    WHERE id=%s

                    LIMIT 1
                    """,
                    (
                        order["id"],
                    )
                )


                order = cursor.fetchone()


        # =================================================
        # RENDER
        # =================================================

        return render_template(
            "order_tracking.html",
            order=order,
            error=error
        )


    finally:

        cursor.close()
        conn.close()