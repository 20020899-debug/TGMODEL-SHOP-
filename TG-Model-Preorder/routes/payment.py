from flask import Blueprint, render_template

payment_bp = Blueprint(
    "payment",
    __name__
)


@payment_bp.route("/payment/success")
def payment_success():

    return render_template("payment_success.html")


@payment_bp.route("/payment/cancel")
def payment_cancel():

    return render_template("payment_cancel.html")