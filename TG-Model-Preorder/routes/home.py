from flask import Blueprint
from flask import render_template

from config import products

home_bp = Blueprint(
    "home",
    __name__
)


@home_bp.route("/")
def home():

    return render_template(
        "index.html",
        products=products
    )


@home_bp.route("/preorder/<int:id>")
def preorder(id):

    product = None

    for p in products:

        if p["id"] == id:

            product = p
            break


    if product is None:

        return "Không tìm thấy sản phẩm"


    return render_template(
        "preorder.html",
        product=product
    )
