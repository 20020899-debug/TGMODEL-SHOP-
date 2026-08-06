from flask import Blueprint, render_template, request
import sqlite3


payment_bp = Blueprint(
    "payment",
    __name__
)


@payment_bp.route("/payment/success")
def payment_success():
    return render_template(
        "payment_success.html"
    )


@payment_bp.route("/payment/cancel")
def payment_cancel():
    return render_template(
        "payment_cancel.html"
    )


@payment_bp.route(
    "/payment/webhook",
    methods=["POST"]
)
def webhook():

    data = request.json

    print("PAYOS WEBHOOK:", data)


    if not data:
        return "No data", 400


    # PayOS báo thanh toán thành công
    if data.get("code") == "00":

        order_code = (
            data
            .get("data", {})
            .get("description")
        )


        if order_code:

            conn = sqlite3.connect(
                "orders.db"
            )

            cursor = conn.cursor()


            cursor.execute(
                """
                UPDATE orders

                SET status = ?

                WHERE order_code = ?

                AND status = ?

                """,
                (
                    "Đã cọc",
                    order_code,
                    "Chưa thanh toán"
                )
            )


            print(
                "UPDATED:",
                cursor.rowcount,
                order_code
            )


            conn.commit()
            conn.close()


    return "OK", 200
