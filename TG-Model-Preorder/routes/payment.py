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


    print("====================")
    print("PAYOS WEBHOOK")
    print("====================")



    data = request.json


    print(data)



    if not data:

        return "No data", 400



    # Thanh toán thành công

    if data.get("code") == "00":


        try:


            # Lấy mã đơn shop
            # description = TGM001

            order_code = (
                data
                .get("data", {})
                .get("description")
            )



            if not order_code:


                print(
                    "KHONG CO ORDER CODE"
                )


                return "OK",200



            print(
                "UPDATE:",
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
                    "Đã thanh toán",
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


            return "ERROR",500



    else:


        print(
            "PAYMENT NOT SUCCESS"
        )



    return "OK",200
