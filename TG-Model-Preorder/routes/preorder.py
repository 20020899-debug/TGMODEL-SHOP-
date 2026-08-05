from flask import Blueprint, request, render_template
import sqlite3
from datetime import datetime

from config import products

preorder_bp = Blueprint(
    "preorder",
    __name__
)


@preorder_bp.route("/submit", methods=["POST"])
def submit():

    # Lấy id sản phẩm
    product_id = int(request.form.get("product_id"))

    # Tìm sản phẩm trong config.py
    product = None

    for p in products:

        if p["id"] == product_id:
            product = p
            break

    if product is None:
        return "Không tìm thấy sản phẩm"

    fullname = request.form.get("fullname")
    phone = request.form.get("phone")
    contact = request.form.get("contact")

    province = request.form.get("province")
    district = request.form.get("district")
    ward = request.form.get("ward")
    address_detail = request.form.get("address_detail")

    quantity = int(request.form.get("quantity", 1))

    note = request.form.get("note")

    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM orders"
    )

    count = cursor.fetchone()[0] + 1

    order_code = f"TG{count:04d}"

    created_at = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    cursor.execute("""
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
        contact=contact,

        province=province,
        district=district,
        ward=ward,
        address_detail=address_detail,

        quantity=quantity,
        note=note,

        status="Chưa thanh toán",

        product=product
    )
