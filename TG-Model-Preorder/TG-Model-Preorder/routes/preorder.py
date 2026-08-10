from flask import (
    Blueprint,
    request,
    redirect,
    make_response,
    render_template
)

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import time
import secrets

from database import get_db
from config import products
from payos_service import payos


# =========================================================
# MÚI GIỜ VIỆT NAM
# =========================================================

VIETNAM_TZ = ZoneInfo(
    "Asia/Ho_Chi_Minh"
)


preorder_bp = Blueprint(
    "preorder",
    __name__
)


# =========================================================
# CHUẨN HÓA THỜI GIAN DATABASE
# =========================================================

def normalize_expires_at(expires_at):

    if expires_at is None:
        return None

    # Database đang lưu TIMESTAMP không timezone.
    # Quy ước giá trị trong DB là giờ Việt Nam.

    if expires_at.tzinfo is None:

        expires_at = expires_at.replace(
            tzinfo=VIETNAM_TZ
        )

    else:

        expires_at = expires_at.astimezone(
            VIETNAM_TZ
        )

    return expires_at


# =========================================================
# TRANG PRE-ORDER
# =========================================================

@preorder_bp.route(
    "/preorder/<int:product_id>"
)
def preorder(product_id):

    # =====================================================
    # TÌM SẢN PHẨM
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
    # KIỂM TRA ĐƠN CŨ BẰNG COOKIE
    # =====================================================

    order_token = request.cookies.get(
        "order_token"
    )

    existing_order = None


    if order_token:

        conn = get_db()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    order_code,
                    product_name,
                    quantity,
                    deposit,
                    payment_url,
                    expires_at,
                    status

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

            order = cursor.fetchone()


            if order:

                expires_at = (
                    normalize_expires_at(
                        order[5]
                    )
                )

                now_vn = datetime.now(
                    VIETNAM_TZ
                )


                # =========================================
                # CÒN HẠN
                # =========================================

                if (
                    expires_at
                    and expires_at > now_vn
                ):

                    existing_order = order


                # =========================================
                # HẾT HẠN
                # =========================================

                else:

                    cursor.execute(
                        """
                        UPDATE orders

                        SET status=%s

                        WHERE order_code=%s
                        AND status=%s
                        """,
                        (
                            "Hết hạn thanh toán",
                            order[0],
                            "Chưa thanh toán"
                        )
                    )

                    conn.commit()


        finally:

            cursor.close()
            conn.close()


    # =====================================================
    # HIỂN THỊ TRANG
    # =====================================================

    return render_template(
        "preorder.html",
        product=product,
        existing_order=existing_order
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
    # LẤY SẢN PHẨM
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
    # THÔNG TIN KHÁCH
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
        # COOKIE
        # =================================================

        order_token = request.cookies.get(
            "order_token"
        )

        existing_order = None


        # =================================================
        # TÌM ĐƠN THEO COOKIE
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

                now_vn = datetime.now(
                    VIETNAM_TZ
                )


                if (
                    candidate_expires_at
                    and
                    candidate_expires_at > now_vn
                ):

                    existing_order = candidate


                else:

                    cursor.execute(
                        """
                        UPDATE orders

                        SET status=%s

                        WHERE order_code=%s
                        AND status=%s
                        """,
                        (
                            "Hết hạn thanh toán",
                            candidate[0],
                            "Chưa thanh toán"
                        )
                    )

                    conn.commit()


        # =================================================
        # TÌM ĐƠN THEO SĐT
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

                now_vn = datetime.now(
                    VIETNAM_TZ
                )


                if (
                    candidate_expires_at
                    and
                    candidate_expires_at > now_vn
                ):

                    existing_order = candidate


                else:

                    cursor.execute(
                        """
                        UPDATE orders

                        SET status=%s

                        WHERE order_code=%s
                        AND status=%s
                        """,
                        (
                            "Hết hạn thanh toán",
                            candidate[0],
                            "Chưa thanh toán"
                        )
                    )

                    conn.commit()


        # =================================================
        # ĐÃ CÓ ĐƠN CÒN HẠN
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
        # TẠO MÃ ĐƠN
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
        # TOKEN
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
        # THỜI GIAN VIỆT NAM
        # =================================================

        created_time = datetime.now(
            VIETNAM_TZ
        )


        created_at = (
            created_time.strftime(
                "%d/%m/%Y %H:%M:%S"
            )
        )


        # =================================================
        # HẾT HẠN SAU 15 PHÚT
        # =================================================

        expires_time = (
            created_time
            + timedelta(
                minutes=15
            )
        )


        # Database lưu TIMESTAMP
        # không timezone,
        # nhưng quy ước là giờ Việt Nam.

        expires_at_db = (
            expires_time.replace(
                tzinfo=None
            )
        )


     

        # =================================================
        # INSERT ORDER
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
                expires_at_db,

                None,
                new_order_token
            )
        )


        conn.commit()


        # =================================================
        # TẠO PAYOS
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


        conn.commit()


        # =================================================
        # REDIRECT PAYOS
        # =================================================

        response = make_response(
            redirect(
                payment_url
            )
        )


        # =================================================
        # COOKIE
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


    except Exception:

        conn.rollback()

        raise


    finally:

        cursor.close()
        conn.close()

