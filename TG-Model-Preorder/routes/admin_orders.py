from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from psycopg2.extras import RealDictCursor

from database import get_db

from services.order_service import (
    normalize_expires_at,
    is_order_expired,
    mark_order_expired
)

from services.stock_service import (
    release_stock
)


admin_orders_bp = Blueprint(
    "admin_orders",
    __name__
)


# =========================================================
# TRẠNG THÁI HỢP LỆ
# =========================================================

ALLOWED_STATUSES = (
    "Chưa thanh toán",
    "Đã cọc",
    "Đã chuyển khoản full",
    "Đang chuẩn bị hàng",
    "Đã gửi hàng",
    "Hoàn thành",
    "Đã hủy",
    "Hết hạn thanh toán"
)


# =========================================================
# CHI TIẾT ĐƠN HÀNG
# =========================================================

@admin_orders_bp.route(
    "/admin/order/<int:id>"
)
def order_detail(id):

    # =====================================================
    # KIỂM TRA ĐĂNG NHẬP
    # =====================================================

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        cursor.execute(
            """
            SELECT *

            FROM orders

            WHERE id=%s

            LIMIT 1
            """,
            (
                id,
            )
        )


        order = cursor.fetchone()


        if order is None:

            return (
                "Không tìm thấy đơn hàng",
                404
            )


        # =================================================
        # KIỂM TRA HẾT HẠN
        # =================================================

        if order["status"] == "Chưa thanh toán":

            expires_at = (
                normalize_expires_at(
                    order["expires_at"]
                )
            )


            if is_order_expired(
                expires_at
            ):

                mark_order_expired(
                    cursor,
                    conn,
                    order["order_code"]
                )


                # =========================================
                # ĐỌC LẠI SAU KHI UPDATE
                # =========================================

                cursor.execute(
                    """
                    SELECT *

                    FROM orders

                    WHERE id=%s

                    LIMIT 1
                    """,
                    (
                        id,
                    )
                )


                order = cursor.fetchone()


        return render_template(
            "order_detail.html",
            order=order
        )


    finally:

        cursor.close()
        conn.close()


# =========================================================
# CẬP NHẬT ĐƠN HÀNG
#
# - trạng thái
# - mã vận đơn
# =========================================================

@admin_orders_bp.route(
    "/admin/order/<int:id>/update",
    methods=["POST"]
)
def update_order(id):

    # =====================================================
    # KIỂM TRA ADMIN
    # =====================================================

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    # =====================================================
    # TRẠNG THÁI
    # =====================================================

    new_status = request.form.get(
        "status",
        ""
    ).strip()


    if new_status not in ALLOWED_STATUSES:

        return (
            "Trạng thái không hợp lệ",
            400
        )


    # =====================================================
    # MÃ VẬN ĐƠN
    # =====================================================

    tracking_code = request.form.get(
        "tracking_code",
        ""
    ).strip()


    if not tracking_code:

        tracking_code = None


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        # =================================================
        # KHÓA DÒNG ĐƠN TRONG LÚC UPDATE
        # =================================================

        cursor.execute(
            """
            SELECT
                id,
                order_code,
                status,
                product_id,
                quantity,
                stock_reserved,
                tracking_code

            FROM orders

            WHERE id=%s

            LIMIT 1

            FOR UPDATE
            """,
            (
                id,
            )
        )


        order = cursor.fetchone()


        if order is None:

            return (
                "Không tìm thấy đơn hàng",
                404
            )


        old_status = (
            order["status"]
        )


        product_id = (
            order["product_id"]
        )


        quantity = (
            order["quantity"]
        )


        stock_reserved = (
            order["stock_reserved"]
        )


        # =================================================
        # CHƯA THANH TOÁN
        # →
        # HỦY / HẾT HẠN
        #
        # HOÀN TỒN KHO
        # =================================================

        if (
            old_status == "Chưa thanh toán"
            and
            new_status in (
                "Đã hủy",
                "Hết hạn thanh toán"
            )
        ):

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
                        + str(
                            order["order_code"]
                        )
                    )


            cursor.execute(
                """
                UPDATE orders

                SET
                    status=%s,
                    tracking_code=%s,
                    stock_reserved=FALSE

                WHERE id=%s
                """,
                (
                    new_status,
                    tracking_code,
                    id
                )
            )


        # =================================================
        # CHƯA THANH TOÁN
        # →
        # ĐÃ CỌC / ĐÃ CHUYỂN KHOẢN FULL
        #
        # HÀNG ĐÃ TRỪ TỪ LÚC TẠO ĐƠN
        # =================================================

        elif (
            old_status == "Chưa thanh toán"
            and
            new_status in (
                "Đã cọc",
                "Đã chuyển khoản full"
            )
        ):

            cursor.execute(
                """
                UPDATE orders

                SET
                    status=%s,
                    tracking_code=%s,
                    stock_reserved=FALSE

                WHERE id=%s
                """,
                (
                    new_status,
                    tracking_code,
                    id
                )
            )


        # =================================================
        # CÁC TRƯỜNG HỢP KHÁC
        #
        # Bao gồm:
        # - giữ nguyên status nhưng nhập mã vận đơn
        # - Đã cọc → Đang chuẩn bị hàng
        # - Đang chuẩn bị hàng → Đã gửi hàng
        # - ...
        # =================================================

        else:

            cursor.execute(
                """
                UPDATE orders

                SET
                    status=%s,
                    tracking_code=%s

                WHERE id=%s
                """,
                (
                    new_status,
                    tracking_code,
                    id
                )
            )


        conn.commit()


    except Exception:

        conn.rollback()

        raise


    finally:

        cursor.close()
        conn.close()


    return redirect(
        url_for(
            "admin_orders.order_detail",
            id=id
        )
    )


# =========================================================
# XÓA ĐƠN
# =========================================================

@admin_orders_bp.route(
    "/admin/order/<int:id>/delete",
    methods=["POST"]
)
def delete_order(id):

    # =====================================================
    # KIỂM TRA ADMIN
    # =====================================================

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        # =================================================
        # LẤY ĐƠN
        # =================================================

        cursor.execute(
            """
            SELECT
                product_id,
                quantity,
                stock_reserved

            FROM orders

            WHERE id=%s

            LIMIT 1

            FOR UPDATE
            """,
            (
                id,
            )
        )


        order = cursor.fetchone()


        # =================================================
        # ĐƠN VẪN GIỮ HÀNG
        # → HOÀN KHO TRƯỚC KHI XÓA
        # =================================================

        if (
            order
            and
            order["stock_reserved"]
            and
            order["product_id"] is not None
            and
            order["quantity"] is not None
            and
            order["quantity"] > 0
        ):

            released = release_stock(
                cursor,
                order["product_id"],
                order["quantity"]
            )


            if not released:

                raise RuntimeError(
                    "Không thể hoàn tồn kho trước khi xóa đơn"
                )


        # =================================================
        # XÓA
        # =================================================

        cursor.execute(
            """
            DELETE FROM orders

            WHERE id=%s
            """,
            (
                id,
            )
        )


        conn.commit()


    except Exception:

        conn.rollback()

        raise


    finally:

        cursor.close()
        conn.close()


    return redirect(
        url_for(
            "admin.admin"
        )
    )