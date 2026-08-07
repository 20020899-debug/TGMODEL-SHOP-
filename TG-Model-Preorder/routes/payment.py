from flask import Blueprint, render_template, request, make_response

from database import get_db


payment_bp = Blueprint(
    "payment",
    __name__
)


# =========================================================
# THANH TOÁN THÀNH CÔNG
# =========================================================

@payment_bp.route("/payment/success")
def payment_success():

    return render_template(
        "payment_success.html"
    )


# =========================================================
# HỦY THANH TOÁN
# =========================================================

@payment_bp.route("/payment/cancel")
def payment_cancel():

    order_token = request.cookies.get(
        "order_token"
    )

    if order_token:

        conn = get_db()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                UPDATE orders

                SET status=%s

                WHERE order_token=%s
                AND status=%s
                """,
                (
                    "Đã hủy",
                    order_token,
                    "Chưa thanh toán"
                )
            )

            print(
                "CANCEL UPDATED ROW:",
                cursor.rowcount
            )

            conn.commit()

        except Exception:

            conn.rollback()

            cursor.close()
            conn.close()

            raise

        cursor.close()
        conn.close()


    response = make_response(
        render_template(
            "payment_cancel.html"
        )
    )

    response.delete_cookie(
        "order_token"
    )

    return response


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
    # LẤY DỮ LIỆU PAYOS
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
    # KIỂM TRA THANH TOÁN THÀNH CÔNG
    # =====================================================

    if data.get("code") != "00":

        print(
            "PAYMENT NOT SUCCESS"
        )

        return "OK", 200


    # =====================================================
    # LẤY MÃ ĐƠN TGMODEL
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
    # KẾT NỐI DATABASE
    # =====================================================

    conn = get_db()
    cursor = conn.cursor()


    try:

        # =================================================
        # TÌM ĐƠN HÀNG
        # =================================================

        cursor.execute(
            """
            SELECT
                id,
                status

            FROM orders

            WHERE order_code=%s

            LIMIT 1
            """,
            (
                order_code,
            )
        )


        order = cursor.fetchone()


        # =================================================
        # KHÔNG TÌM THẤY ĐƠN
        # =================================================

        if order is None:

            print(
                "KHONG TIM THAY DON:",
                order_code
            )

            cursor.close()
            conn.close()

            return "OK", 200


        order_id = order[0]

        current_status = order[1]


        print(
            "ORDER ID:",
            order_id
        )

        print(
            "CURRENT STATUS:",
            current_status
        )


        # =================================================
        # ĐƠN ĐÃ CỌC
        # =================================================

        if current_status == "Đã cọc":

            print(
                "DON DA COC TRUOC DO"
            )

            cursor.close()
            conn.close()

            return "OK", 200


        # =================================================
        # ĐƠN ĐÃ HỦY
        # =================================================

        if current_status == "Đã hủy":

            print(
                "DON DA BI HUY"
            )

            cursor.close()
            conn.close()

            return "OK", 200


        # =================================================
        # THANH TOÁN THÀNH CÔNG
        #
        # Không kiểm tra expires_at ở đây.
        #
        # Nếu PayOS gửi webhook với code = 00
        # thì xác nhận thanh toán thành công.
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
            "PAYMENT UPDATED ROW:",
            cursor.rowcount
        )


        conn.commit()


        print(
            "PAYMENT SUCCESS:",
            order_code
        )


        cursor.close()
        conn.close()


        return "OK", 200


    except Exception:

        conn.rollback()

        cursor.close()
        conn.close()

        raise
