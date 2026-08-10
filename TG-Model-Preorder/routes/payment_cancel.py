from flask import (
    Blueprint,
    render_template,
    request,
    make_response
)

from database import get_db

from services.stock_service import (
    release_stock
)


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


    # =====================================================
    # CÓ COOKIE ĐƠN
    # =====================================================

    if order_token:

        conn = get_db()
        cursor = conn.cursor()


        try:

            # =================================================
            # LẤY ĐƠN CHƯA THANH TOÁN
            # =================================================

            cursor.execute(
                """
                SELECT
                    id,
                    order_code,
                    product_id,
                    quantity,
                    stock_reserved,
                    status

                FROM orders

                WHERE order_token=%s

                ORDER BY id DESC

                LIMIT 1
                """,
                (
                    order_token,
                )
            )


            order = cursor.fetchone()


            # =================================================
            # CÓ ĐƠN
            # =================================================

            if order:

                order_id = order[0]
                order_code = order[1]
                product_id = order[2]
                quantity = order[3]
                stock_reserved = order[4]
                status = order[5]


                # =============================================
                # CHỈ HỦY ĐƠN CHƯA THANH TOÁN
                # =============================================

                if status == "Chưa thanh toán":

                    # =========================================
                    # TRẢ HÀNG VỀ KHO
                    # =========================================

                    if (
                        stock_reserved
                        and
                        product_id is not None
                        and
                        quantity is not None
                        and
                        quantity > 0
                    ):

                        released = release_stock(
                            cursor,
                            product_id,
                            quantity
                        )


                        if not released:

                            raise RuntimeError(
                                "Không thể hoàn tồn kho cho đơn "
                                + str(order_code)
                            )


                    # =========================================
                    # CẬP NHẬT ĐƠN
                    # =========================================

                    cursor.execute(
                        """
                        UPDATE orders

                        SET
                            status=%s,
                            stock_reserved=FALSE

                        WHERE id=%s
                        AND status=%s
                        """,
                        (
                            "Đã hủy",
                            order_id,
                            "Chưa thanh toán"
                        )
                    )


                    conn.commit()


                    print(
                        "CANCEL ORDER:",
                        order_code
                    )


                    print(
                        "CANCEL UPDATED ROW:",
                        cursor.rowcount
                    )


        except Exception:

            conn.rollback()

            raise


        finally:

            cursor.close()
            conn.close()


    # =====================================================
    # TRANG HỦY THANH TOÁN
    # =====================================================

    response = make_response(
        render_template(
            "payment_cancel.html"
        )
    )


    # =====================================================
    # XÓA COOKIE
    # =====================================================

    response.delete_cookie(
        "order_token"
    )


    return response
