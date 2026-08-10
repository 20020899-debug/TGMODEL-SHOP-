from flask import Blueprint, render_template


payment_success_bp = Blueprint(
    "payment_success",
    __name__
)


# =========================================================
# THANH TOÁN THÀNH CÔNG
# =========================================================

@payment_success_bp.route(
    "/payment/success"
)
def payment_success():

    return render_template(
        "payment_success.html"
    )