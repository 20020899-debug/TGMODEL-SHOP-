from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from database import get_db
from io import BytesIO
from flask import send_file
from openpyxl import Workbook

admin_bp = Blueprint(
    "admin",
    __name__
)



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


    cursor = conn.cursor()


    keyword = request.args.get(
        "keyword",
        ""
    ).strip()



    if keyword:


        cursor.execute(
        """
        SELECT *
        FROM orders

        WHERE
        order_code LIKE ?
        OR fullname LIKE ?
        OR phone LIKE ?

        ORDER BY id DESC

        """,
        (
            f"%{keyword}%",
            f"%{keyword}%",
            f"%{keyword}%"
        ))


    else:


        cursor.execute(
        """
        SELECT *
        FROM orders

        ORDER BY id DESC
        """
        )


    orders = cursor.fetchall()


    conn.close()



    return render_template(
        "admin.html",
        orders=orders,
        keyword=keyword
    )




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


    cursor = conn.cursor()



    cursor.execute(
        """
        SELECT *
        FROM orders
        WHERE id=?
        """,
        (id,)
    )


    order = cursor.fetchone()


    conn.close()



    return render_template(
        "order_detail.html",
        order=order
    )





@admin_bp.route(
    "/admin/order/<int:id>/update",
    methods=["POST"]
)
def update_order(id):


    if not session.get("admin"):

        return redirect(
            url_for("auth.login")
        )



    status = request.form.get(
        "status"
    )



    conn = sqlite3.connect(
        "orders.db"
    )

    cursor = conn.cursor()



    cursor.execute(
        """
        UPDATE orders

        SET status=?

        WHERE id=?

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
    
@admin_bp.route("/admin/order/<int:id>/delete", methods=["POST"])
def delete_order(id):

    if not session.get("admin"):
        return redirect(
            url_for("auth.login")
        )


    conn = sqlite3.connect(
        "orders.db"
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        DELETE FROM orders
        WHERE id=?
        """,
        (id,)
    )


    conn.commit()
    conn.close()


    return redirect(
        url_for("admin.admin")
    )
    
@admin_bp.route("/admin/export")
def export_excel():

    if not session.get("admin"):
        return redirect(
            url_for("auth.login")
        )

    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        ORDER BY id DESC
    """)

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
