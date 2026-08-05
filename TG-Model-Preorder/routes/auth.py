from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session

from config import ADMIN_USERNAME
from config import ADMIN_PASSWORD

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect(url_for("admin.admin"))

        return render_template(
            "login.html",
            error="Sai tài khoản hoặc mật khẩu!"
        )

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect(url_for("auth.login"))