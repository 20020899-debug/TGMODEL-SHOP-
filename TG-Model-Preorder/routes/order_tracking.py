from flask import Blueprint, render_template, request
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
# THEO DÕI ĐƠN HÀNG
#
# Khách có thể:
# - tự xem đơn gần nhất bằng cookie
# - tra cứu bằng mã đơn + số điện thoại
#
# Đối với Pre-order đã cọc:
# - hiển thị tổng giá trị đơn
# - số tiền đã cọc
# - số tiền còn phải thanh toán
# =========================================================

@order_tracking_bp.route(
    "/order-status",
    methods=["GET", "POST"]
)
def order_status():

    order_token = request.cookies.get("order_token")

    order = None
    error = None

    # =====================================================
    # DATABASE
    # =====================================================

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)


    try:

        # =================================================
        # TRA CỨU BẰNG MÃ ĐƠN + SỐ ĐIỆN THOẠI
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


            if not order_code or not phone:

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
                        "Không tìm thấy đơn hàng phù hợp."
                    )


        # =================================================
        # TỰ TÌM ĐƠN GẦN NHẤT THEO COOKIE
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
                (order_token,)
            )

            order = cursor.fetchone()


        # =================================================
        # KIỂM TRA HẠN THANH TOÁN BAN ĐẦU
        #
        # Chỉ đơn "Chưa thanh toán" mới có hạn 15 phút.
        #
        # Không áp dụng cho:
        # - Chờ xác nhận
        # - Đã cọc
        # - Chờ thanh toán phần còn lại
        # - Đã thanh toán đủ
        # =================================================

        if (
            order
            and order["status"] == "Chưa thanh toán"
        ):

            expires_at = normalize_expires_at(
                order["expires_at"]
            )


            if is_order_expired(expires_at):

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
                    (order["id"],)
                )

                order = cursor.fetchone()


        # =================================================
        # THÔNG TIN THANH TOÁN
        #
        # Tính tại server để template chỉ cần hiển thị.
        # =================================================

        total_amount = 0
        paid_amount = 0
        remaining_amount = 0


        if order:

            price = order["price"] or 0
            deposit = order["deposit"] or 0
            quantity = order["quantity"] or 1

            total_amount = price * quantity


            # =============================================
            # KHÁCH CHỌN THANH TOÁN FULL NGAY TỪ ĐẦU
            # =============================================

            if order["payment_type"] == "full":

                if order["status"] in (
                    "Đã chuyển khoản full",
                    "Đã thanh toán đủ",
                    "Đang chuẩn bị hàng",
                    "Đã gửi hàng",
                    "Hoàn thành"
                ):
                    paid_amount = total_amount


            # =============================================
            # KHÁCH CHỌN CỌC
            # =============================================

            elif order["payment_type"] == "deposit":

                # =========================================
                # ĐÃ THANH TOÁN ĐỦ
                # =========================================

                if order["status"] in (
                    "Đã thanh toán đủ",
                    "Đang chuẩn bị hàng",
                    "Đã gửi hàng",
                    "Hoàn thành"
                ):
                    paid_amount = total_amount


                # =========================================
                # ĐÃ CỌC / ĐANG CHỜ THANH TOÁN CÒN LẠI
                # =========================================

                elif order["status"] in (
                    "Đã cọc",
                    "Chờ thanh toán phần còn lại"
                ):
                    paid_amount = deposit * quantity


                # =========================================
                # ĐƠN CỌC 0Đ ĐÃ ĐƯỢC ADMIN XÁC NHẬN
                # =========================================

                elif order["status"] == "Chờ xác nhận":
                    paid_amount = 0


            remaining_amount = max(
                total_amount - paid_amount,
                0
            )


        # =================================================
        # HIỂN THỊ TRANG THEO DÕI
        # =================================================

        return render_template(
            "order_tracking.html",
            order=order,
            error=error,
            total_amount=total_amount,
            paid_amount=paid_amount,
            remaining_amount=remaining_amount
        )


    finally:

        cursor.close()
        conn.close()
