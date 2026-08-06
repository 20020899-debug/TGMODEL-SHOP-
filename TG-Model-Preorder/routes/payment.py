from flask import Blueprint, render_template, request
import sqlite3


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

    print("==============================")
    print("PAYOS WEBHOOK RECEIVED")
    print("==============================")


    data = request.json


    print("DATA:")
    print(data)



    if not data:

        print("NO DATA")

        return "No data", 400



    # PayOS thanh toán thành công

    if data.get("code") == "00":


        try:


            payos_order_code = data["data"]["orderCode"]


            # Đổi sang mã đơn của shop
            # 1 -> TGM001
            # 2 -> TGM002

            order_code = f"TGM{payos_order_code:03d}"


            print(
                "UPDATE ORDER:",
                order_code
            )



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



            print(
                "UPDATED ROW:",
                cursor.rowcount
            )



            conn.commit()

            conn.close()



        except Exception as e:


            print(
                "WEBHOOK ERROR:",
                e
            )


            return "Error", 500



    else:


        print(
            "PAYMENT NOT SUCCESS"
        )



    return "OK", 200
