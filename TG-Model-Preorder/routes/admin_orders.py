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
    "Chờ xác nhận",
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
# TRẠNG THÁI ĐÃ XÁC NHẬN
#
# Khi vào các trạng thái này:
# - hàng đã được trừ từ lúc tạo đơn
# - không được hoàn kho khi xóa lịch sử
# =========================================================

CONFIRMED_STATUSES = (
    "Đã cọc",
    "Đã chuyển khoản full",
    "Đang chuẩn bị hàng",
    "Đã gửi hàng",
    "Hoàn thành"
)


# =========================================================
# TRẠNG THÁI HỦY
# =========================================================

CANCEL_STATUSES = (
    "Đã hủy",
    "Hết hạn thanh toán"
)


# =========================================================
# TRẠNG THÁI ĐANG GIỮ HÀNG
#
# stock_reserved có thể vẫn TRUE
# =========================================================

RESERVED_STATUSES = (
    "Chờ xác nhận",
    "Chưa thanh toán"
)


# =========================================================
# CHI TIẾT ĐƠN
# =========================================================

@admin_orders_bp.route(
    "/admin/order/<int:id>"
)
def order_detail(id):

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
        # CHỈ "CHƯA THANH TOÁN" MỚI CÓ HẠN 15 PHÚT
        #
        # "Chờ xác nhận" không tự hết hạn.
        # =================================================

        if order["status"] == "Chưa thanh toán":

            expires_at = normalize_expires_at(
                order["expires_at"]
            )


            if is_order_expired(
                expires_at
            ):

                mark_order_expired(
                    cursor,
                    conn,
                    order["order_code"]
                )


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
# CẬP NHẬT ĐƠN
#
# - trạng thái
# - mã vận đơn
# =========================================================

@admin_orders_bp.route(
    "/admin/order/<int:id>/update",
    methods=["POST"]
)
def update_order(id):

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    new_status = request.form.get(
        "status",
        ""
    ).strip()


    if new_status not in ALLOWED_STATUSES:

        return (
            "Trạng thái không hợp lệ",
            400
        )


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
        # KHÓA DÒNG
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
        # ĐƠN ĐANG GIỮ HÀNG
        # →
        # HỦY / HẾT HẠN
        #
        # HOÀN KHO
        #
        # Áp dụng cho:
        # - Chờ xác nhận
        # - Chưa thanh toán
        # =================================================

        if (
            old_status in RESERVED_STATUSES
            and
            new_status in CANCEL_STATUSES
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
        # ĐƠN ĐANG GIỮ HÀNG
        # →
        # ĐÃ XÁC NHẬN
        #
        # KHÔNG TRỪ THÊM HÀNG
        # CHỈ BỎ stock_reserved
        #
        # Áp dụng cho cả:
        # - Chờ xác nhận
        # - Chưa thanh toán
        # =================================================

        elif (
            old_status in RESERVED_STATUSES
            and
            new_status in CONFIRMED_STATUSES
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
        # ĐẢM BẢO ĐƠN ĐÃ XÁC NHẬN
        # KHÔNG CÒN GIỮ STOCK
        # =================================================

        elif new_status in CONFIRMED_STATUSES:

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
        # Ví dụ:
        # - chỉ sửa mã vận đơn
        # - đổi Chờ xác nhận ↔ Chưa thanh toán
        # - đổi giữa các trạng thái hủy
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
        # KHÓA ĐƠN
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
        # XÓA ĐƠN
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
