from flask import Blueprint, request, redirect, make_response
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time
import secrets

from database import get_db
from config import products
from payos_service import payos


preorder_bp = Blueprint(
    "preorder",
    __name__
)


# =========================================================
# TẠO ĐƠN HÀNG
# =========================================================

@preorder_bp.route(
    "/submit",
    methods=["POST"]
)
def submit():

    # =====================================================
    # Lấy sản phẩm
    # =====================================================

    try:
        product_id = int(
            request.form.get("product_id")
        )

    except (TypeError, ValueError):

        return "Sản phẩm không hợp lệ", 400


    product = next(
        (
            p for p in products
            if p["id"] == product_id
        ),
        None
    )


    if product is None:

        return "Không tìm thấy sản phẩm", 404


    # =====================================================
    # Thông tin khách hàng
    # =====================================================

    fullname = request.form.get(
        "fullname",
        ""
    ).strip()


    phone = request.form.get(
        "phone",
        ""
    ).strip()


    contact = request.form.get(
        "contact",
        ""
    ).strip()


    province = request.form.get(
        "province",
        ""
    ).strip()


    district = request.form.get(
        "district",
        ""
    ).strip()


    ward = request.form.get(
        "ward",
        ""
    ).strip()


    address_detail = request.form.get(
        "address_detail",
        ""
    ).strip()


    try:

        quantity = int(
            request.form.get(
                "quantity",
                1
            )
        )

    except (TypeError, ValueError):

        quantity = 1


    if quantity < 1:

        quantity = 1


    note = request.form.get(
        "note",
        ""
    ).strip()


    # =====================================================
    # Kết nối PostgreSQL
    # =====================================================

    conn = get_db()

    cursor = conn.cursor()


    try:

        # =================================================
        # KIỂM TRA COOKIE ORDER TOKEN
        # =================================================

        order_token = request.cookies.get(
            "order_token"
        )


        existing_order = None


        if order_token:

            cursor.execute(
                """
                SELECT
                    order_code,
                    payment_url,
                    expires_at,
                    status
                FROM orders
                WHERE order_token=%s
                AND status=%s
                AND expires_at > NOW()
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    order_token,
                    "Chưa thanh toán"
                )
            )


            existing_order = cursor.fetchone()


        # =================================================
        # NẾU COOKIE KHÔNG CÓ ĐƠN
        # THÌ KIỂM TRA THÊM BẰNG SĐT
        # =================================================

        if existing_order is None and phone:

            cursor.execute(
                """
                SELECT
                    order_code,
                    payment_url,
                    expires_at,
                    status,
                    order_token
                FROM orders
                WHERE phone=%s
                AND status=%s
                AND expires_at > NOW()
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    phone,
                    "Chưa thanh toán"
                )
            )


            existing_order = cursor.fetchone()


        # =================================================
        # ĐÃ CÓ ĐƠN CHƯA THANH TOÁN CÒN HẠN
        # =================================================

        if existing_order:

            old_order_code = existing_order[0]
            old_payment_url = existing_order[1]
            old_expires_at = existing_order[2]


            # ---------------------------------------------
            # Nếu đã có link PayOS
            # ---------------------------------------------

            if old_payment_url:

                response = make_response(
                    redirect(old_payment_url)
                )


                # Ghi lại token vào cookie
                # nếu khách tìm thấy đơn bằng SĐT

                old_token = None

                if len(existing_order) >= 5:

                    old_token = existing_order[4]


                if old_token:

                    response.set_cookie(
                        "order_token",
                        old_token,
                        max_age=60 * 60 * 24 * 30,
                        httponly=True,
                        samesite="Lax",
                        secure=True
                    )


                return response


            # ---------------------------------------------
            # Trường hợp có đơn nhưng chưa có payment URL
            # ---------------------------------------------

            return f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Đơn hàng đang chờ thanh toán</title>
            </head>

            <body>

                <h2>Bạn đang có một đơn hàng chưa thanh toán</h2>

                <p>
                    Mã đơn:
                    <b>{old_order_code}</b>
                </p>

                <p>
                    Đơn hàng này vẫn còn thời gian thanh toán.
                </p>

                <p>
                    Vui lòng quay lại trang thanh toán.
                </p>

                <a href="/">
                    Quay lại trang chủ
                </a>

            </body>
            </html>
            """, 400


        # =================================================
        # TẠO MÃ ĐƠN SHOP
        # =================================================

        cursor.execute(
            """
            SELECT COALESCE(MAX(id), 0)
            FROM orders
            """
        )


        last_id = cursor.fetchone()[0]


        order_id = last_id + 1


        order_code = f"TGM{order_id:03d}"


        # =================================================
        # TẠO TOKEN NGẪU NHIÊN
        # =================================================

        new_order_token = secrets.token_urlsafe(32)


        # =================================================
        # MÃ PAYOS
        # =================================================

        payos_order_code = int(
            time.time()
        )


        # =================================================
        # THỜI GIAN
        # =================================================

        created_time = datetime.now(
            ZoneInfo("Asia/Ho_Chi_Minh")
        )


        created_at = created_time.strftime(
            "%d/%m/%Y %H:%M:%S"
        )


        # 15 PHÚT

        expires_at = (
            created_time
            + timedelta(minutes=15)
        )


        # =================================================
        # TẠO ĐƠN TRONG DATABASE
        # =================================================

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

                created_at,
                expires_at,

                payment_url,
                order_token
            )

            VALUES
            (
                %s,

                %s,%s,%s,

                %s,%s,%s,%s,

                %s,%s,

                %s,%s,

                %s,%s,

                %s,

                %s,%s,

                %s,%s
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
                expires_at,

                None,
                new_order_token
            )
        )


        conn.commit()


        # =================================================
        # TẠO THANH TOÁN PAYOS
        # =================================================

        payment_data = {

            "orderCode":
                payos_order_code,

            "amount":
                product["deposit"] * quantity,

            "description":
                order_code,

            "returnUrl":
                "https://tgmodel-shop.onrender.com/payment/success",

            "cancelUrl":
                "https://tgmodel-shop.onrender.com/payment/cancel",
            # PayOS tự hết hạn cùng thời điểm với đơn hàng
            "expiredAt": int(expires_at.timestamp())

        }


        payment_link = (
            payos.payment_requests.create(
                payment_data
            )
        )


        payment_url = (
            payment_link.checkout_url
        )


        # =================================================
        # LƯU PAYMENT URL
        # =================================================

        cursor.execute(
            """
            UPDATE orders

            SET payment_url=%s

            WHERE order_code=%s
            """,
            (
                payment_url,
                order_code
            )
        )


        conn.commit()


        # =================================================
        # ĐÓNG DATABASE
        # =================================================

        cursor.close()
        conn.close()


        # =================================================
        # CHUYỂN SANG PAYOS
        # =================================================

        response = make_response(
            redirect(payment_url)
        )


        # =================================================
        # LƯU TOKEN VÀO COOKIE
        # =================================================

        response.set_cookie(
            "order_token",
            new_order_token,

            max_age=60 * 60 * 24 * 30,

            httponly=True,

            samesite="Lax",

            secure=True
        )


        return response


    except Exception:

        conn.rollback()

        cursor.close()
        conn.close()

        raise
