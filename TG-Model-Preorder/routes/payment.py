from flask import Blueprint, render_template, request


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

    print("========== PAYOS WEBHOOK ==========")


    data = request.get_json()

    print(data)


    if not data:

        return "NO DATA", 400



    # PayOS báo thành công

    if data.get("code") == "00":


        payos_order_code = (
            data
            .get("data", {})
            .get("orderCode")
        )


        if not payos_order_code:

            print("KHONG CO ORDER CODE")

            return "OK", 200



        # Đổi mã PayOS -> mã shop
        # Ví dụ:
        # PayOS: 15
        # Shop: TGM015

        order_code = f"TGM{int(payos_order_code):03d}"


        print(
            "UPDATE ORDER:",
            order_code
        )


        from database import get_db

        conn = get_db()

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



    else:

        print(
            "PAYMENT NOT SUCCESS"
        )


    return "OK",200
