from flask import Blueprint, render_template, request
import sqlite3
import os
import hmac
import hashlib
import json


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
# PayOS Webhook
# =========================

@payment_bp.route(
    "/payment/webhook",
    methods=["POST"]
)
def webhook():

    data = request.json


    if not data:

        return "No data", 400



    # PayOS gửi trạng thái thành công code = 00

    if data.get("code") == "00":


        order_code = data["data"]["orderCode"]


        order_code = f"TG{order_code:06d}"



        conn = sqlite3.connect(
            "orders.db"
        )

        cursor = conn.cursor()



        cursor.execute(
            """
            UPDATE orders

            SET status=?

            WHERE order_code=?

            """,
            (
                "Đã cọc",
                order_code
            )
        )



        conn.commit()
        conn.close()



    return "OK", 200
