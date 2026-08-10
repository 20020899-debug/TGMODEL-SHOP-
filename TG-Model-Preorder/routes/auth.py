import os

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)


auth_bp = Blueprint(
    "auth",
    __name__
)


# =========================================================
# TÀI KHOẢN ADMIN
#
# Lấy từ Environment Variables của Render
# =========================================================

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)


ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "123456"
)


# =========================================================
# ĐĂNG NHẬP
# =========================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # =====================================================
    # POST - XỬ LÝ ĐĂNG NHẬP
    # =====================================================

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()


        password = request.form.get(
            "password",
            ""
        )


        # =================================================
        # ĐÚNG TÀI KHOẢN
        # =================================================

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["admin"] = True


            return redirect(
                url_for(
                    "admin.admin"
                )
            )


        # =================================================
        # SAI TÀI KHOẢN
        # =================================================

        return render_template(
            "login.html",
            error=(
                "Sai tài khoản hoặc mật khẩu!"
            )
        )


    # =====================================================
    # GET - HIỂN THỊ TRANG LOGIN
    # =====================================================

    return render_template(
        "login.html"
    )


# =========================================================
# ĐĂNG XUẤT
# =========================================================

@auth_bp.route(
    "/logout"
)
def logout():

    session.pop(
        "admin",
        None
    )


    return redirect(
        url_for(
            "auth.login"
        )
    )
