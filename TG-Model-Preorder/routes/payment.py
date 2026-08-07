from flask import Blueprint, render_template, request, make_response
from datetime import datetime
from zoneinfo import ZoneInfo

from database import get_db


payment_bp = Blueprint(
    "payment",
    __name__
)


# =========================================================
# THANH TOÁN THÀNH CÔNG
# =========================================================

@payment_bp.route(
    "/payment/success"
)
def payment_success():

    return render_template(
        "payment_success.html"
    )


# =========================================================
# HỦY THANH TOÁN
# =========================================================

@payment_bp.route(
    "/payment/cancel"
)
def payment_cancel():

    return render_template(
        "payment_cancel.html"
    )


# =========================================================
# WEBHOOK PAYOS
# =========================================================

@payment_bp.route(
    "/payment/webhook",
    methods=["POST"]
)
def webhook():

    print(
        "========== PAYOS WEBHOOK =========="
    )


    # =====================================================
    # Lấy dữ liệu PayOS
    # =====================================================

    data = request.get_json()


    print(
        "PAYOS DATA:",
        data
    )


    if not data:

        print(
            "KHONG CO DATA"
        )

        return "NO DATA", 400


    # =====================================================
    # Kiểm tra thanh toán thành công
    # =====================================================

    if data.get("code") != "00":

        print(
            "PAYMENT NOT SUCCESS"
        )

        return "OK", 200


    # =====================================================
    # Lấy description
    # =====================================================

    order_code = (
        data
        .get("data", {})
        .get("description")
    )


    if not order_code:

        print(
            "KHONG CO DESCRIPTION"
        )

        return "OK", 200


    print(
        "ORDER:",
        order_code
    )


    # =====================================================
    # Kết nối database
    # =====================================================

    conn = get_db()

    cursor = conn.cursor()


    try:

        # =================================================
        # Lấy đơn hàng
        # =================================================

        cursor.execute(
            """
            SELECT
                id,
                status,
                expires_at
            FROM orders
            WHERE order_code=%s
            LIMIT 1
            """,
            (
                order_code,
            )
        )


        order = cursor.fetchone()


        if order is None:

            print(
                "KHONG TIM THAY DON:",
                order_code
            )

            conn.close()

            return "OK", 200


        order_id = order[0]

        current_status = order[1]

        expires_at = order[2]


        print(
            "ORDER ID:",
            order_id
        )

        print(
            "STATUS:",
            current_status
        )

        print(
            "EXPIRES AT:",
            expires_at
        )


        # =================================================
        # Nếu đơn đã cọc rồi
        # =================================================

        if current_status == "Đã cọc":

            print(
                "DON DA THANH TOAN TRUOC DO"
            )

            conn.close()

            return "OK", 200


        # =================================================
        # Nếu đơn đã bị hủy
        # =================================================

        if current_status == "Đã hủy":

            print(
                "DON DA HUY"
            )

            conn.close()

            return "OK", 200


        # =================================================
        # Kiểm tra thời hạn
        # =================================================

        now = datetime.now(
            ZoneInfo("Asia/Ho_Chi_Minh")
        )


        # PostgreSQL TIMESTAMP không timezone
        # nên nếu expires_at không có timezone
        # thì gắn múi giờ Việt Nam vào

        if expires_at is not None:

            if expires_at.tzinfo is None:

                expires_at = expires_at.replace(
                    tzinfo=ZoneInfo(
                        "Asia/Ho_Chi_Minh"
                    )
                )


        # =================================================
        # ĐÃ HẾT HẠN
        # =================================================

        if (
            expires_at is not None
            and now >= expires_at
        ):

            print(
                "DON DA HET HAN THANH TOAN"
            )


            cursor.execute(
                """
                UPDATE orders

                SET status=%s

                WHERE id=%s
                AND status=%s
                """,
                (
                    "Hết hạn thanh toán",
                    order_id,
                    "Chưa thanh toán"
                )
            )


            conn.commit()

            conn.close()


            return "OK", 200


        # =================================================
        # THANH TOÁN HỢP LỆ
        # =================================================

        cursor.execute(
            """
            UPDATE orders

            SET status=%s

            WHERE id=%s
            AND status=%s
            """,
            (
                "Đã cọc",
                order_id,
                "Chưa thanh toán"
            )
        )


        print(
            "UPDATED ROW:",
            cursor.rowcount
        )


        conn.commit()

        conn.close()


        print(
            "PAYMENT SUCCESS:",
            order_code
        )


        return "OK", 200


    except Exception:

        conn.rollback()

        conn.close()

        raise
