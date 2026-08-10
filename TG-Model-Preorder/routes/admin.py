from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file
)

from io import BytesIO

from openpyxl import Workbook

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


admin_bp = Blueprint(
    "admin",
    __name__
)


# =========================================================
# DANH SÁCH ĐƠN HÀNG
# =========================================================

@admin_bp.route(
    "/admin"
)
def admin():

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

        # =================================================
        # TÌM CÁC ĐƠN CHƯA THANH TOÁN
        # =================================================

        cursor.execute(
            """
            SELECT
                order_code,
                expires_at

            FROM orders

            WHERE status=%s
            """,
            (
                "Chưa thanh toán",
            )
        )


        pending_orders = cursor.fetchall()


        # =================================================
        # KIỂM TRA QUÁ HẠN
        #
        # Không UPDATE trực tiếp vì phải hoàn tồn kho.
        # =================================================

        for pending_order in pending_orders:

            expires_at = (
                normalize_expires_at(
                    pending_order["expires_at"]
                )
            )


            if is_order_expired(
                expires_at
            ):

                mark_order_expired(
                    cursor,
                    conn,
                    pending_order["order_code"]
                )


        # =================================================
        # TÌM KIẾM
        # =================================================

        keyword = request.args.get(
            "keyword",
            ""
        ).strip()


        status = request.args.get(
            "status",
            ""
        ).strip()


        sql = """
        SELECT *

        FROM orders

        WHERE 1=1
        """


        params = []


        # =================================================
        # TÌM THEO TỪ KHÓA
        # =================================================

        if keyword:

            sql += """
            AND
            (
                order_code ILIKE %s
                OR fullname ILIKE %s
                OR phone ILIKE %s
            )
            """


            params.extend(
                [
                    f"%{keyword}%",
                    f"%{keyword}%",
                    f"%{keyword}%"
                ]
            )


        # =================================================
        # LỌC TRẠNG THÁI
        # =================================================

        if status:

            sql += """
            AND status=%s
            """


            params.append(
                status
            )


        # =================================================
        # SẮP XẾP
        # =================================================

        sql += """
        ORDER BY id DESC
        """


        cursor.execute(
            sql,
            tuple(params)
        )


        orders = cursor.fetchall()


        # =================================================
        # RENDER
        # =================================================

        return render_template(
            "admin.html",
            orders=orders,
            keyword=keyword,
            status=status
        )


    finally:

        cursor.close()

        conn.close()


# =========================================================
# CHI TIẾT ĐƠN HÀNG
# =========================================================

@admin_bp.route(
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
        # NẾU ĐƠN CHƯA THANH TOÁN NHƯNG ĐÃ HẾT HẠN
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
                # ĐỌC LẠI ĐƠN SAU KHI UPDATE
                # =========================================

                cursor.execute(
                    """
                    SELECT *

                    FROM orders

                    WHERE id=%s
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
# CẬP NHẬT TRẠNG THÁI THỦ CÔNG
# =========================================================

@admin_bp.route(
    "/admin/order/<int:id>/update",
    methods=["POST"]
)
def update_order(id):

    # =====================================================
    # KIỂM TRA ĐĂNG NHẬP
    # =====================================================

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


    # =====================================================
    # DANH SÁCH TRẠNG THÁI HỢP LỆ
    # =====================================================

    allowed_statuses = (
        "Chưa thanh toán",
        "Đã cọc",
        "Đã chuyển khoản full",
        "Đang chuẩn bị hàng",
        "Đã gửi hàng",
        "Hoàn thành",
        "Đã hủy",
        "Hết hạn thanh toán"
    )


    if new_status not in allowed_statuses:

        return (
            "Trạng thái không hợp lệ",
            400
        )


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        # =================================================
        # LẤY TRẠNG THÁI CŨ + THÔNG TIN TỒN KHO
        # =================================================

        cursor.execute(
            """
            SELECT
                id,
                order_code,
                status,
                product_id,
                quantity,
                stock_reserved

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


        old_status = order["status"]

        product_id = order["product_id"]

        quantity = order["quantity"]

        stock_reserved = order["stock_reserved"]


        # =================================================
        # KHÔNG THAY ĐỔI
        # =================================================

        if new_status == old_status:

            return redirect(
                url_for(
                    "admin.order_detail",
                    id=id
                )
            )


        # =================================================
        # CHƯA THANH TOÁN
        # →
        # ĐÃ HỦY / HẾT HẠN
        #
        # PHẢI HOÀN TỒN KHO
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
                    stock_reserved=FALSE

                WHERE id=%s
                """,
                (
                    new_status,
                    id
                )
            )


        # =================================================
        # CHƯA THANH TOÁN
        # →
        # ĐÃ CỌC / ĐÃ CHUYỂN FULL
        #
        # HÀNG ĐÃ TRỪ RỒI
        # KHÔNG TRỪ THÊM
        # KHÔNG HOÀN KHO
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
                    stock_reserved=FALSE

                WHERE id=%s
                """,
                (
                    new_status,
                    id
                )
            )


        # =================================================
        # CÁC TRẠNG THÁI KHÁC
        #
        # Chỉ đổi status.
        # =================================================

        else:

            cursor.execute(
                """
                UPDATE orders

                SET status=%s

                WHERE id=%s
                """,
                (
                    new_status,
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
            "admin.order_detail",
            id=id
        )
    )


# =========================================================
# XÓA ĐƠN HÀNG
# =========================================================

@admin_bp.route(
    "/admin/order/<int:id>/delete",
    methods=["POST"]
)
def delete_order(id):

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

        # =================================================
        # LẤY ĐƠN TRƯỚC KHI XÓA
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
            """,
            (
                id,
            )
        )


        order = cursor.fetchone()


        if order:

            # =============================================
            # NẾU ĐƠN VẪN ĐANG GIỮ HÀNG
            # THÌ PHẢI HOÀN KHO TRƯỚC KHI XÓA
            # =============================================

            if (
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


# =========================================================
# XUẤT EXCEL
# =========================================================

@admin_bp.route(
    "/admin/export"
)
def export_excel():

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

            ORDER BY id DESC
            """
        )


        orders = cursor.fetchall()


    finally:

        cursor.close()

        conn.close()


    # =====================================================
    # TẠO EXCEL
    # =====================================================

    wb = Workbook()

    ws = wb.active

    ws.title = "Đơn hàng"


    # =====================================================
    # HEADER
    # =====================================================

    ws.append(
        [
            "Mã đơn",
            "Ngày tạo",
            "Khách hàng",
            "SĐT",
            "Facebook/Zalo",
            "Sản phẩm",
            "Số lượng",
            "Giá",
            "Tiền cọc",
            "Hình thức thanh toán",
            "Số tiền thanh toán",
            "Trạng thái",
            "Tỉnh",
            "Quận",
            "Phường",
            "Địa chỉ",
            "Ghi chú"
        ]
    )


    # =====================================================
    # DATA
    # =====================================================

    for order in orders:

        quantity = (
            order["quantity"]
            or 1
        )


        # =================================================
        # TÍNH SỐ TIỀN THANH TOÁN
        # =================================================

        if order["payment_type"] == "full":

            payment_type_text = (
                "Chuyển khoản full"
            )


            payment_amount = (
                (order["price"] or 0)
                * quantity
            )

        else:

            payment_type_text = (
                "Cọc một phần"
            )


            payment_amount = (
                (order["deposit"] or 0)
                * quantity
            )


        ws.append(
            [
                order["order_code"],
                order["created_at"],
                order["fullname"],
                order["phone"],
                order["contact"],
                order["product_name"],
                order["quantity"],
                order["price"],
                order["deposit"],
                payment_type_text,
                payment_amount,
                order["status"],
                order["province"],
                order["district"],
                order["ward"],
                order["address_detail"],
                order["note"]
            ]
        )


    # =====================================================
    # FILE
    # =====================================================

    output = BytesIO()

    wb.save(
        output
    )

    output.seek(
        0
    )


    return send_file(
        output,
        as_attachment=True,
        download_name="don_hang.xlsx",
        mimetype=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )
