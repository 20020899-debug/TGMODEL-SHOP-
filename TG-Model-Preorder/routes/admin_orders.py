from flask import Blueprint, render_template, request, redirect, url_for, session
from psycopg2.extras import RealDictCursor

from database import get_db

from services.order_service import (
    normalize_expires_at,
    is_order_expired,
    mark_order_expired
)

from services.stock_service import release_stock


admin_orders_bp = Blueprint("admin_orders", __name__)


# =========================================================
# TRẠNG THÁI HỢP LỆ
#
# Luồng Pre-order có cọc:
#
# Đã cọc
#     ↓
# Chờ thanh toán phần còn lại
#     ↓
# Đã thanh toán đủ
#     ↓
# Đang chuẩn bị hàng
#     ↓
# Đã gửi hàng
#     ↓
# Hoàn thành
# =========================================================

ALLOWED_STATUSES = (
    "Chờ xác nhận",
    "Chưa thanh toán",
    "Đã cọc",
    "Chờ thanh toán phần còn lại",
    "Đã thanh toán đủ",
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
# Khi đơn đã vào các trạng thái này:
#
# - hàng đã được trừ từ lúc tạo đơn
# - stock_reserved phải là FALSE
# - không được hoàn kho khi chỉ xóa lịch sử đơn
#
# "Chờ thanh toán phần còn lại" cũng là đơn đã cọc,
# vì vậy tuyệt đối không coi đây là đơn chưa thanh toán.
# =========================================================

CONFIRMED_STATUSES = (
    "Đã cọc",
    "Chờ thanh toán phần còn lại",
    "Đã thanh toán đủ",
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
# Chỉ áp dụng cho giai đoạn trước khi đơn được xác nhận.
#
# stock_reserved có thể vẫn TRUE.
# =========================================================

RESERVED_STATUSES = (
    "Chờ xác nhận",
    "Chưa thanh toán"
)


# =========================================================
# CHI TIẾT ĐƠN
# =========================================================

@admin_orders_bp.route("/admin/order/<int:id>")
def order_detail(id):

    # =====================================================
    # KIỂM TRA ĐĂNG NHẬP ADMIN
    # =====================================================

    if not session.get("admin"):
        return redirect(url_for("auth.login"))


    # =====================================================
    # DATABASE
    # =====================================================

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)


    try:

        # =================================================
        # LẤY ĐƠN HÀNG
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM orders
            WHERE id=%s
            LIMIT 1
            """,
            (id,)
        )

        order = cursor.fetchone()


        if order is None:
            return "Không tìm thấy đơn hàng", 404


        # =================================================
        # KIỂM TRA HẠN THANH TOÁN BAN ĐẦU
        #
        # Chỉ trạng thái "Chưa thanh toán" mới sử dụng
        # expires_at của lần thanh toán đầu tiên.
        #
        # Không áp dụng cơ chế này cho:
        #
        # - Đã cọc
        # - Chờ thanh toán phần còn lại
        # - Đã thanh toán đủ
        #
        # Link thanh toán phần còn lại hết hạn sẽ được
        # xử lý riêng và KHÔNG làm đơn bị hủy.
        # =================================================

        if order["status"] == "Chưa thanh toán":

            expires_at = normalize_expires_at(order["expires_at"])

            if is_order_expired(expires_at):

                mark_order_expired(
                    cursor,
                    conn,
                    order["order_code"]
                )

                # =========================================
                # ĐỌC LẠI ĐƠN SAU KHI UPDATE
                # =========================================

                cursor.execute(
                    """
                    SELECT *
                    FROM orders
                    WHERE id=%s
                    LIMIT 1
                    """,
                    (id,)
                )

                order = cursor.fetchone()


        # =================================================
        # HIỂN THỊ CHI TIẾT
        # =================================================

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
# Admin có thể:
#
# - đổi trạng thái
# - nhập / sửa mã vận đơn
#
# Đối với Pre-order:
#
# Admin đổi:
#
# Đã cọc
#     ↓
# Chờ thanh toán phần còn lại
#
# thì khách sẽ được phép thanh toán số tiền còn lại
# ở trang Theo dõi đơn hàng.
# =========================================================

@admin_orders_bp.route(
    "/admin/order/<int:id>/update",
    methods=["POST"]
)
def update_order(id):

    # =====================================================
    # KIỂM TRA ĐĂNG NHẬP ADMIN
    # =====================================================

    if not session.get("admin"):
        return redirect(url_for("auth.login"))


    # =====================================================
    # DỮ LIỆU FORM
    # =====================================================

    new_status = request.form.get("status", "").strip()

    if new_status not in ALLOWED_STATUSES:
        return "Trạng thái không hợp lệ", 400


    tracking_code = request.form.get("tracking_code", "").strip()

    if not tracking_code:
        tracking_code = None


    # =====================================================
    # DATABASE
    # =====================================================

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)


    try:

        # =================================================
        # KHÓA ĐƠN TRONG LÚC CẬP NHẬT
        #
        # FOR UPDATE tránh hai thao tác đồng thời làm sai
        # trạng thái hoặc tồn kho.
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
            (id,)
        )

        order = cursor.fetchone()


        if order is None:
            return "Không tìm thấy đơn hàng", 404


        old_status = order["status"]
        product_id = order["product_id"]
        quantity = order["quantity"]
        stock_reserved = order["stock_reserved"]


        # =================================================
        # ĐƠN ĐANG GIỮ HÀNG → HỦY / HẾT HẠN
        #
        # Áp dụng cho:
        #
        # - Chờ xác nhận
        # - Chưa thanh toán
        #
        # Hàng đã bị trừ khi tạo đơn nên phải hoàn kho.
        # =================================================

        if (
            old_status in RESERVED_STATUSES
            and new_status in CANCEL_STATUSES
        ):

            if (
                stock_reserved
                and product_id is not None
                and quantity is not None
                and quantity > 0
            ):

                released = release_stock(
                    cursor,
                    product_id,
                    quantity
                )

                if not released:
                    raise RuntimeError(
                        "Không thể hoàn tồn kho cho đơn "
                        + str(order["order_code"])
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
        # ĐƠN ĐANG GIỮ HÀNG → ĐÃ XÁC NHẬN
        #
        # Hàng đã được trừ khi tạo đơn.
        #
        # Vì vậy:
        #
        # - KHÔNG trừ kho lần nữa
        # - KHÔNG hoàn kho
        # - chỉ bỏ stock_reserved
        # =================================================

        elif (
            old_status in RESERVED_STATUSES
            and new_status in CONFIRMED_STATUSES
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
        # ĐƠN ĐÃ XÁC NHẬN
        #
        # Bao gồm:
        #
        # - Đã cọc
        # - Chờ thanh toán phần còn lại
        # - Đã thanh toán đủ
        # - Đã chuyển khoản full
        # - Đang chuẩn bị hàng
        # - Đã gửi hàng
        # - Hoàn thành
        #
        # Luôn đảm bảo stock_reserved = FALSE.
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
        #
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


        # =================================================
        # LƯU THAY ĐỔI
        # =================================================

        conn.commit()


    except Exception:

        conn.rollback()
        raise


    finally:
        cursor.close()
        conn.close()


    # =====================================================
    # QUAY LẠI CHI TIẾT ĐƠN
    # =====================================================

    return redirect(
        url_for(
            "admin_orders.order_detail",
            id=id
        )
    )


# =========================================================
# XÓA ĐƠN
#
# Nếu đơn vẫn đang giữ hàng:
# → hoàn kho trước khi xóa.
#
# Nếu đơn đã được xác nhận:
# → chỉ xóa lịch sử, KHÔNG hoàn kho.
# =========================================================

@admin_orders_bp.route(
    "/admin/order/<int:id>/delete",
    methods=["POST"]
)
def delete_order(id):

    # =====================================================
    # KIỂM TRA ĐĂNG NHẬP ADMIN
    # =====================================================

    if not session.get("admin"):
        return redirect(url_for("auth.login"))


    # =====================================================
    # DATABASE
    # =====================================================

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)


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
            (id,)
        )

        order = cursor.fetchone()


        # =================================================
        # ĐƠN VẪN GIỮ HÀNG
        # → HOÀN KHO TRƯỚC KHI XÓA
        # =================================================

        if (
            order
            and order["stock_reserved"]
            and order["product_id"] is not None
            and order["quantity"] is not None
            and order["quantity"] > 0
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
            (id,)
        )

        conn.commit()


    except Exception:

        conn.rollback()
        raise


    finally:
        cursor.close()
        conn.close()


    # =====================================================
    # QUAY LẠI DANH SÁCH ĐƠN
    # =====================================================

    return redirect(url_for("admin.admin"))
