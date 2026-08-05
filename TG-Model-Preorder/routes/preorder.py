from flask import Blueprint, request, render_template
import sqlite3
from datetime import datetime


preorder_bp = Blueprint(
    "preorder",
    __name__
)


# ==========================
# HIỂN THỊ FORM PREORDER
# ==========================

@preorder_bp.route("/preorder/<int:id>")
def preorder(id):

    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE id=?
        """,
        (id,)
    )


    product = cursor.fetchone()


    conn.close()


    return render_template(
        "preorder.html",
        product=product
    )



# ==========================
# NHẬN ĐƠN
# ==========================

@preorder_bp.route("/submit", methods=["POST"])
def submit():


    product_id = request.form.get("product_id")


    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()



    # lấy sản phẩm

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE id=?
        """,
        (product_id,)
    )


    product = cursor.fetchone()



    fullname = request.form.get("fullname")

    phone = request.form.get("phone")

    contact = request.form.get("contact")


    province = request.form.get("province")

    district = request.form.get("district")

    ward = request.form.get("ward")

    address_detail = request.form.get("address_detail")


    quantity = int(
        request.form.get("quantity",1)
    )


    note = request.form.get("note")



    cursor.execute(
        "SELECT COUNT(*) FROM orders"
    )


    count = cursor.fetchone()[0] + 1


    order_code = f"TG{count:06d}"



    created_at = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )



    cursor.execute(
    """
    INSERT INTO orders
    (
        order_code,
        fullname,
        phone,
        contact,
        province,
        district,
        ward,
        address_detail,
        quantity,
        note,
        product_name,
        product_brand,
        price,
        deposit,
        status,
        created_at
    )

    VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """,
    (
        order_code,
        fullname,
        phone,
        contact,
        province,
        district,
        ward,
        address_detail,
        quantity,
        note,

        product["name"],
        product["brand"],
        product["price"],
        product["deposit"],

        "Chưa thanh toán",

        created_at
    ))




    conn.commit()
    conn.close()



    return render_template(
        "success.html",

        order_code=order_code,

        fullname=fullname,

        phone=phone,

        product=product,

        status="Chưa thanh toán"
    )