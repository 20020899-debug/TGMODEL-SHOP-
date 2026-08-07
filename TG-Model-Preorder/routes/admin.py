from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import send_file

from io import BytesIO
from openpyxl import Workbook

from database import get_db
from psycopg2.extras import RealDictCursor


admin_bp = Blueprint(
    "admin",
    __name__
)


# =========================
# Danh sách đơn hàng
# =========================

@admin_bp.route("/admin")
def admin():

    if not session.get("admin"):

        return redirect(
            url_for("auth.login")
        )


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # =========================
    # Tự chuyển đơn quá hạn
    # =========================

    cursor.execute(
        """
        UPDATE orders

        SET status=%s

        WHERE status=%s

        AND expires_at < NOW()
        """,
        (
            "Hết hạn thanh toán",
            "Chưa thanh toán"
        )
    )

    conn.commit()


    # =========================
    # Tìm kiếm
    # =========================

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


if keyword:

    sql += """
    AND
    (
        order_code ILIKE %s
        OR fullname ILIKE %s
        OR phone ILIKE %s
    )
    """

    params.extend([
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    ])


if status:

    sql += """
    AND status=%s
    """

    params.append(status)


sql += """
ORDER BY id DESC
"""

cursor.execute(
    sql,
    tuple(params)
)

    orders = cursor.fetchall()

    conn.close()


    return render_template(
        "admin.html",
        orders=orders,
        keyword=keyword
    )
# =========================
# Chi tiết đơn hàng
# =========================

@admin_bp.route("/admin/order/<int:id>")
def order_detail(id):

    if not session.get("admin"):

        return redirect(
            url_for("auth.login")
        )


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    cursor.execute(
        """
        SELECT *

        FROM orders

        WHERE id=%s
        """,
        (id,)
    )


    order = cursor.fetchone()

    conn.close()


    if order is None:

        return "Không tìm thấy đơn hàng", 404


    return render_template(
        "order_detail.html",
        order=order
    )


# =========================
# Cập nhật trạng thái
# =========================

@admin_bp.route(
    "/admin/order/<int:id>/update",
    methods=["POST"]
)
def update_order(id):

    if not session.get("admin"):

        return redirect(
            url_for("auth.login")
        )


    status = request.form.get("status")


    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE orders

        SET status=%s

        WHERE id=%s
        """,
        (
            status,
            id
        )
    )


    conn.commit()
    conn.close()


    return redirect(
        url_for(
            "admin.order_detail",
            id=id
        )
    )


# =========================
# Xóa đơn hàng
# =========================

@admin_bp.route(
    "/admin/order/<int:id>/delete",
    methods=["POST"]
)
def delete_order(id):

    if not session.get("admin"):

        return redirect(
            url_for("auth.login")
        )


    conn = get_db()

    cursor = conn.cursor()


    cursor.execute(
        """
        DELETE

        FROM orders

        WHERE id=%s
        """,
        (id,)
    )


    conn.commit()
    conn.close()


    return redirect(
        url_for("admin.admin")
    )


# =========================
# Xuất Excel
# =========================

@admin_bp.route("/admin/export")
def export_excel():

    if not session.get("admin"):

        return redirect(
            url_for("auth.login")
        )


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    cursor.execute(
        """
        SELECT *

        FROM orders

        ORDER BY id DESC
        """
    )


    orders = cursor.fetchall()

    conn.close()


    wb = Workbook()

    ws = wb.active

    ws.title = "Đơn hàng"


    ws.append([
        "Mã đơn",
        "Ngày tạo",
        "Khách hàng",
        "SĐT",
        "Facebook/Zalo",
        "Sản phẩm",
        "Số lượng",
        "Giá",
        "Tiền cọc",
        "Trạng thái",
        "Tỉnh",
        "Quận",
        "Phường",
        "Địa chỉ",
        "Ghi chú"
    ])


    for order in orders:

        ws.append([
            order["order_code"],
            order["created_at"],
            order["fullname"],
            order["phone"],
            order["contact"],
            order["product_name"],
            order["quantity"],
            order["price"],
            order["deposit"],
            order["status"],
            order["province"],
            order["district"],
            order["ward"],
            order["address_detail"],
            order["note"]
        ])


    output = BytesIO()

    wb.save(output)

    output.seek(0)


    return send_file(
        output,
        as_attachment=True,
        download_name="don_hang.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
