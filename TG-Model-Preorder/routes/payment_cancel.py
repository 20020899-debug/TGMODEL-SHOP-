from flask import (
    Blueprint,
    render_template,
    request,
    make_response
)

from database import get_db


payment_cancel_bp = Blueprint(
    "payment_cancel",
    __name__
)


# =========================================================
# HỦY THANH TOÁN
# =========================================================

@payment_cancel_bp.route(
    "/payment/cancel"
)
def payment_cancel():

    order_token = request.cookies.get(
        "order_token"
    )


    if order_token:

        conn = get_db()
        cursor = conn.cursor()


        try:

            cursor.execute(
                """
                UPDATE orders

                SET status=%s

                WHERE order_token=%s
                AND status=%s
                """,
                (
                    "Đã hủy",
                    order_token,
                    "Chưa thanh toán"
                )
            )


            print(
                "CANCEL UPDATED ROW:",
                cursor.rowcount
            )


            conn.commit()


        except Exception:

            conn.rollback()

            raise


        finally:

            cursor.close()
            conn.close()


    # =====================================================
    # HIỂN THỊ TRANG HỦY
    # =====================================================

    response = make_response(
        render_template(
            "payment_cancel.html"
        )
    )


    # =====================================================
    # XÓA COOKIE ĐƠN
    # =====================================================

    response.delete_cookie(
        "order_token"
    )


    return response