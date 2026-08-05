from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session

import sqlite3


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


    conn = sqlite3.connect(
        "orders.db"
    )

    conn.row_factory = sqlite3.Row


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


    conn = sqlite3.connect(
        "orders.db"
    )

    conn.row_factory = sqlite3.Row


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
