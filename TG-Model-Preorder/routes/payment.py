from flask import Blueprint, render_template

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
@payment_bp.route("/payment/webhook", methods=["POST"])
def webhook():

    data = request.json

    order_code = data["data"]["orderCode"]

    status = data["code"]


    if status == "00":

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
                f"TG{order_code:06d}"
            )
        )


        conn.commit()
        conn.close()


    return "OK"
