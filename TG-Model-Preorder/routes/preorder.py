from flask import Blueprint, request, redirect
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time

from database import get_db
from config import products
from payos_service import payos

preorder_bp = Blueprint(
    "preorder",
    __name__
)


@preorder_bp.route(
    "/submit",
    methods=["POST"]
)
def submit():

    # =========================
    # Lấy sản phẩm
    # =========================

    product_id = int(request.form.get("product_id"))

    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if product is None:
        return "Không tìm thấy sản phẩm", 404


    # =========================
    # Thông tin khách hàng
    # =========================

    fullname = request.form.get("fullname")
    phone = request.form.get("phone")
    contact = request.form.get("contact")

    province = request.form.get("province")
    district = request.form.get("district")
    ward = request.form.get("ward")
    address_detail = request.form.get("address_detail")

    quantity = int(
        request.form.get("quantity", 1)
    )

    note = request.form.get("note")


    # =========================
    # Kết nối Database
    # =========================

    conn = get_db()
    cursor = conn.cursor()


    # =========================
    # Tạo mã đơn shop
    # =========================

    cursor.execute("""
        SELECT COALESCE(MAX(id), 0)
        FROM orders
    """)

    count = cursor.fetchone()[0] + 1

    order_code = f"TGM{count:03d}"


    # =========================
    # Mã PayOS
    # =========================

    payos_order_code = int(time.time())


    # =========================
    # Thời gian
    # =========================

    created_time = datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    )

    created_at = created_time.strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    expires_at = created_time + timedelta(minutes=30)


    # =========================
    # Lưu đơn hàng
    # =========================

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
            created_at,
            expires_at
        )
        VALUES
        (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
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
        created_at,
        expires_at
    ))

    conn.commit()
    conn.close()


    # =========================
    # Tạo link thanh toán PayOS
    # =========================

    payment_data = {
        "orderCode": payos_order_code,
        "amount": product["deposit"] * quantity,
        "description": order_code,
        "returnUrl": "https://tgmodel-shop.onrender.com/payment/success",
        "cancelUrl": f"https://tgmodel-shop.onrender.com/payment/cancel?order={order_code}"
    }

    payment_link = payos.payment_requests.create(
        payment_data
    )


    # =========================
    # Chuyển sang PayOS
    # =========================

    return redirect(
        payment_link.checkout_url
    )
