from flask import (
    Blueprint,
    request,
    redirect,
    make_response
)

from datetime import timedelta

import time
import secrets

from database import get_db
from config import products
from payos_service import payos

from services.order_service import (
    get_now_vn,
    normalize_expires_at,
    is_order_expired,
    mark_order_expired
)

from services.stock_service import (
    reserve_stock
)


submit_order_bp = Blueprint(
    "submit_order",
    __name__
)

# =========================================================

# TẠO ĐƠN HÀNG

# =========================================================

@submit_order_bp.route(
"/submit",
methods=["POST"]
)
def submit():
# =====================================================
# LẤY PRODUCT ID
# =====================================================

try:

    product_id = int(
        request.form.get(
            "product_id"
        )
    )

except (TypeError, ValueError):

    return (
        "Sản phẩm không hợp lệ",
        400
    )


# =====================================================
# TÌM SẢN PHẨM TRONG CONFIG
# =====================================================

product = next(
    (
        p
        for p in products
        if p["id"] == product_id
    ),
    None
)


if product is None:

    return (
        "Không tìm thấy sản phẩm",
        404
    )


# =====================================================
# THÔNG TIN KHÁCH HÀNG
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


note = request.form.get(
    "note",
    ""
).strip()


# =====================================================
# SỐ LƯỢNG
# =====================================================

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


# =====================================================
# DATABASE
# =====================================================

conn = get_db()
cursor = conn.cursor()


try:

    # =================================================
    # COOKIE ĐƠN HÀNG
    # =================================================

    order_token = request.cookies.get(
        "order_token"
    )


    existing_order = None


    # =================================================
    # KIỂM TRA ĐƠN THEO COOKIE
    # =================================================

    if order_token:

        cursor.execute(
            """
            SELECT
                order_code,
                payment_url,
                expires_at,
                status,
                order_token

            FROM orders

            WHERE order_token=%s
            AND status=%s

            ORDER BY id DESC

            LIMIT 1
            """,
            (
                order_token,
                "Chưa thanh toán"
            )
        )


        candidate = cursor.fetchone()


        if candidate:

            candidate_expires_at = (
                normalize_expires_at(
                    candidate[2]
                )
            )


            # =========================================
            # ĐƠN CŨ ĐÃ HẾT HẠN
            # =========================================

            if is_order_expired(
                candidate_expires_at
            ):

                mark_order_expired(
                    cursor,
                    conn,
                    candidate[0]
                )


            # =========================================
            # ĐƠN CŨ VẪN CÒN HẠN
            # =========================================

            else:

                existing_order = candidate


    # =================================================
    # KIỂM TRA ĐƠN THEO SỐ ĐIỆN THOẠI
    # =================================================

    if (
        existing_order is None
        and phone
    ):

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

            ORDER BY id DESC

            LIMIT 1
            """,
            (
                phone,
                "Chưa thanh toán"
            )
        )


        candidate = cursor.fetchone()


        if candidate:

            candidate_expires_at = (
                normalize_expires_at(
                    candidate[2]
                )
            )


            # =========================================
            # ĐƠN CŨ ĐÃ HẾT HẠN
            # =========================================

            if is_order_expired(
                candidate_expires_at
            ):

                mark_order_expired(
                    cursor,
                    conn,
                    candidate[0]
                )


            # =========================================
            # ĐƠN CŨ VẪN CÒN HẠN
            # =========================================

            else:

                existing_order = candidate


    # =================================================
    # ĐÃ CÓ ĐƠN CHƯA THANH TOÁN CÒN HẠN
    # =================================================

    if existing_order:

        old_order_code = (
            existing_order[0]
        )


        old_payment_url = (
            existing_order[1]
        )


        old_token = (
            existing_order[4]
        )


        # =============================================
        # ĐÃ CÓ LINK PAYOS
        # =============================================

        if old_payment_url:

            response = make_response(
                redirect(
                    old_payment_url
                )
            )


            if old_token:

                response.set_cookie(
                    "order_token",
                    old_token,

                    max_age=
                        60
                        * 60
                        * 24
                        * 30,

                    httponly=True,

                    samesite="Lax",

                    secure=True
                )


            return response


        # =============================================
        # CÓ ĐƠN NHƯNG CHƯA CÓ LINK PAYOS
        # =============================================

        return f"""
        <!DOCTYPE html>

        <html lang="vi">

        <head>

            <meta charset="UTF-8">

            <title>
                Đơn hàng đang chờ thanh toán
            </title>

        </head>

        <body>

            <h2>
                Bạn đang có đơn chưa thanh toán
            </h2>

            <p>
                Mã đơn:
                <b>{old_order_code}</b>
            </p>

            <a href="/">
                Quay lại trang chủ
            </a>

        </body>

        </html>
        """, 400


    # =================================================
    # GIỮ HÀNG / TRỪ TỒN KHO
    #
    # Chỉ tiếp tục tạo đơn nếu kho còn đủ.
    # =================================================

    stock_reserved = reserve_stock(
        cursor,
        product_id,
        quantity
    )


    # =================================================
    # KHÔNG ĐỦ TỒN KHO
    # =================================================

    if not stock_reserved:

        return """
        <!DOCTYPE html>

        <html lang="vi">

        <head>

            <meta charset="UTF-8">

            <title>
                Không đủ hàng
            </title>

        </head>

        <body>

            <h2>
                Sản phẩm không còn đủ số lượng
            </h2>

            <p>
                Số lượng bạn đặt hiện lớn hơn
                số lượng sản phẩm còn trong kho.
            </p>

            <p>
                Vui lòng quay lại trang chủ
                và chọn số lượng nhỏ hơn.
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
        SELECT
            COALESCE(
                MAX(id),
                0
            )

        FROM orders
        """
    )


    last_id = cursor.fetchone()[0]

    order_id = last_id + 1


    order_code = (
        f"TGM{order_id:03d}"
    )


    # =================================================
    # TOKEN ĐƠN HÀNG
    # =================================================

    new_order_token = (
        secrets.token_urlsafe(
            32
        )
    )


    # =================================================
    # MÃ PAYOS
    # =================================================

    payos_order_code = int(
        time.time()
    )


    # =================================================
    # THỜI GIAN HIỆN TẠI
    # =================================================

    created_time = get_now_vn()


    created_at = (
        created_time.strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )


    # =================================================
    # HẠN THANH TOÁN 15 PHÚT
    # =================================================

    expires_time = (
        created_time
        + timedelta(
            minutes=15
        )
    )


    # =================================================
    # DATABASE LƯU GIỜ VIỆT NAM
    # KHÔNG KÈM TIMEZONE
    # =================================================

    expires_at_db = (
        expires_time.replace(
            tzinfo=None
        )
    )


    # =================================================
    # TẠO ĐƠN TRONG DATABASE
    #
    # QUAN TRỌNG:
    #
    # Chưa COMMIT ở đây.
    #
    # Nếu PayOS lỗi thì rollback toàn bộ:
    #
    # - INSERT order
    # - trừ tồn kho
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

            product_id,

            product_name,
            product_brand,

            price,
            deposit,

            status,

            created_at,
            expires_at,

            payment_url,
            order_token,

            stock_reserved
        )

        VALUES
        (
            %s,

            %s,%s,%s,

            %s,%s,%s,%s,

            %s,%s,

            %s,

            %s,%s,

            %s,%s,

            %s,

            %s,%s,

            %s,%s,

            %s
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

            product_id,

            product["name"],
            product["brand"],

            product["price"],
            product["deposit"],

            "Chưa thanh toán",

            created_at,
            expires_at_db,

            None,
            new_order_token,

            True
        )
    )


    # =================================================
    # TẠO LINK THANH TOÁN PAYOS
    # =================================================

    payment_data = {

        "orderCode":
            payos_order_code,

        "amount":
            product["deposit"]
            * quantity,

        "description":
            order_code,

        "returnUrl":
            (
                "https://"
                "tgmodel-shop.onrender.com"
                "/payment/success"
            ),

        "cancelUrl":
            (
                "https://"
                "tgmodel-shop.onrender.com"
                "/payment/cancel"
            ),

        "expiredAt":
            int(
                expires_time.timestamp()
            )
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


    # =================================================
    # COMMIT DUY NHẤT
    #
    # Đến đây mới xác nhận:
    #
    # - trừ kho
    # - tạo đơn
    # - lưu payment URL
    # =================================================

    conn.commit()


    # =================================================
    # CHUYỂN SANG PAYOS
    # =================================================

    response = make_response(
        redirect(
            payment_url
        )
    )


    # =================================================
    # LƯU TOKEN VÀO COOKIE
    # =================================================

    response.set_cookie(
        "order_token",

        new_order_token,

        max_age=
            60
            * 60
            * 24
            * 30,

        httponly=True,

        samesite="Lax",

        secure=True
    )


    return response


# =====================================================
# CÓ LỖI
# =====================================================

except Exception:

    # =================================================
    # ROLLBACK TOÀN BỘ
    #
    # Nếu đã reserve_stock nhưng PayOS lỗi:
    # lượng hàng cũng được hoàn lại vì chưa commit.
    # =================================================

    conn.rollback()

    raise


# =====================================================
# ĐÓNG DATABASE
# =====================================================

finally:

    cursor.close()

    conn.close()
