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
        # KIỂM TRA ĐƠN QUÁ HẠN
        #
        # mark_order_expired sẽ:
        # - đổi trạng thái
        # - hoàn tồn kho nếu cần
        # - bỏ stock_reserved
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
        # TÌM THEO:
        #
        # - mã đơn
        # - khách hàng
        # - số điện thoại
        # - mã vận đơn
        # =================================================

        if keyword:

            sql += """
            AND
            (
                order_code ILIKE %s
                OR fullname ILIKE %s
                OR phone ILIKE %s
                OR tracking_code ILIKE %s
            )
            """


            params.extend(
                [
                    f"%{keyword}%",
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
        # MỚI NHẤT TRƯỚC
        # =================================================

        sql += """
        ORDER BY id DESC
        """


        cursor.execute(
            sql,
            tuple(params)
        )


        orders = cursor.fetchall()


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
            "Mã vận đơn",
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
                order["tracking_code"],
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
