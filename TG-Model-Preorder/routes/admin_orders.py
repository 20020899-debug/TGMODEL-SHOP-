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
# TRẠNG THÁI ĐÃ XÁC NHẬN ĐƠN
#
# Khi chuyển sang các trạng thái này:
# - hàng đã được giữ/trừ từ lúc tạo đơn
# - không được hoàn kho khi xóa đơn về sau
# =========================================================

CONFIRMED_STATUSES = (
    "Đã cọc",
    "Đã chuyển khoản full",
    "Đang chuẩn bị hàng",
    "Đã gửi hàng",
    "Hoàn thành"
)


# =========================================================
# TRẠNG THÁI PHẢI HOÀN KHO
# =========================================================

CANCEL_STATUSES = (
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
        # KIỂM TRA ĐƠN CHƯA THANH TOÁN ĐÃ HẾT HẠN CHƯA
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

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    # =====================================================
    # TRẠNG THÁI MỚI
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
        # KHÓA DÒNG TRƯỚC KHI UPDATE
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


        old_status = order["status"]

        product_id = order["product_id"]

        quantity = order["quantity"]

        stock_reserved = order["stock_reserved"]


        # =================================================
        # CHƯA THANH TOÁN
        # →
        # HỦY / HẾT HẠN
        #
        # PHẢI HOÀN KHO
        # =================================================

        if (
            old_status == "Chưa thanh toán"
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
        # CHƯA THANH TOÁN
        # →
        # ĐƠN ĐÃ ĐƯỢC XÁC NHẬN
        #
        # HÀNG ĐÃ TRỪ TỪ LÚC TẠO ĐƠN
        # KHÔNG TRỪ THÊM
        # CHỈ BỎ CỜ GIỮ HÀNG
        # =================================================

        elif (
            old_status == "Chưa thanh toán"
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
        # ĐANG Ở TRẠNG THÁI ĐÃ XÁC NHẬN
        #
        # ĐẢM BẢO stock_reserved LUÔN FALSE
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
        # - đổi giữa trạng thái hủy/hết hạn
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
        # KHÓA ĐƠN TRƯỚC KHI XÓA
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
        # CHỈ HOÀN KHO NẾU ĐƠN VẪN ĐANG GIỮ HÀNG
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
