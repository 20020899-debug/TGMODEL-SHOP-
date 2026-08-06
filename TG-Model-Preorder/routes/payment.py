from flask import Blueprint, render_template, request
from database import get_db

payment_bp = Blueprint(
    "payment",
    __name__
)


# =========================
# Thanh toán thành công
# =========================

@payment_bp.route("/payment/success")
def payment_success():

    return render_template(
        "payment_success.html"
    )


# =========================
# Hủy thanh toán
# =========================

@payment_bp.route("/payment/cancel")
def payment_cancel():

    return render_template(
        "payment_cancel.html"
    )


# =========================
# Webhook PayOS
# =========================

@payment_bp.route(
    "/payment/webhook",
    methods=["POST"]
)
def webhook():

    print("========== PAYOS WEBHOOK ==========")

    data = request.get_json()

    print(data)

    if not data:
        return "NO DATA", 400

    # Chỉ xử lý khi thanh toán thành công
    if data.get("code") != "00":

        print("PAYMENT NOT SUCCESS")

        return "OK", 200

    # Lấy mã đơn của shop đã gửi trong description
    order_code = (
        data
        .get("data", {})
        .get("description")
    )

    if not order_code:

        print("KHONG CO DESCRIPTION")

        return "OK", 200

    print("ORDER:", order_code)

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status=%s
        WHERE order_code=%s
        """,
        (
            "Đã cọc",
            order_code
        )
    )

    print(
        "UPDATED ROW:",
        cursor.rowcount
    )

    conn.commit()
    conn.close()

    return "OK", 200
