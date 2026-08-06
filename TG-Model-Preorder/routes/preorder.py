from flask import Blueprint, request, redirect
import sqlite3
from datetime import datetime

from config import products
from payos_service import payos


preorder_bp = Blueprint(
    "preorder",
    __name__
)


@preorder_bp.route("/submit", methods=["POST"])
def submit():

    # =========================
    # Lấy sản phẩm
    # =========================

    product_id = int(
        request.form.get("product_id")
    )

    product = None

    for p in products:
        if p["id"] == product_id:
            product = p
            break


    if product is None:
        return "Không tìm thấy sản phẩm"



    # =========================
    # Thông tin khách hàng
    # =========================

    fullname = request.form.get("fullname")
    phone = request.form.get("phone")
    contact = request.form.get("contact")

    province = request.form.get("province")
    district = request.form.get("district")
    ward = request.form.get("ward")

    address_detail = request.form.get(
        "address_detail"
    )


    quantity = int(
        request.form.get(
            "quantity",
            1
        )
    )

    note = request.form.get("note")



    # =========================
    # Lưu đơn hàng
    # =========================

    conn = sqlite3.connect(
        "orders.db"
    )

    cursor = conn.cursor()


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
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
         ?, ?, ?, ?, ?, ?)

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

            "Chờ thanh toán",

            created_at
        )
    )


    conn.commit()
    conn.close()



    # =========================
    # Tạo thanh toán PayOS
    # =========================

    payment_data = {

        "orderCode": count,

        "amount":
            product["deposit"] * quantity,

        "description":
            order_code,

        "returnUrl":
            "https://tgmodel-shop.onrender.com/payment/success",

        "cancelUrl":
            "https://tgmodel-shop.onrender.com/payment/cancel"
    }



    payment_link = payos.payment_requests.create(
        payment_data
    )


    return redirect(
        payment_link.checkout_url
    )
