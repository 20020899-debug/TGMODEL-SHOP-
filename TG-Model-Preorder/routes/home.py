from flask import Blueprint, render_template

from config import product

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def home():

    return render_template(
        "index.html",
        product=product
    )


@home_bp.route("/preorder")
def preorder():

    return render_template(
        "preorder.html",
        product=product
    )