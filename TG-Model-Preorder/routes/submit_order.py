from flask import Blueprint, request, redirect, make_response
from datetime import timedelta

import time
import secrets

from database import get_db
from payos_service import payos

from services.order_service import (
    get_now_vn,
    normalize_expires_at,
    is_order_expired,
    mark_order_expired
)

from services.stock_service import reserve_stock
from services.notification_service import send_new_order_notification


submit_order_bp = Blueprint("submit_order", __name__)


# =========================================================
# TẠO ĐƠN HÀNG
# =========================================================

@submit_order_bp.route("/submit", methods=["POST"])
def submit():

    # =====================================================
    # PRODUCT ID
    # =====================================================

    try:
        product_id = int(request.form.get("product_id"))
    except (TypeError, ValueError):
        return "Sản phẩm không hợp lệ", 400


    # =====================================================
    # THÔNG TIN KHÁCH
    # =====================================================

    fullname = request.form.get("fullname", "").strip()
    phone = request.form.get("phone", "").strip()
    contact = request.form.get("contact", "").strip()

    province = request.form.get("province", "").strip()
    district = request.form.get("district", "").strip()
    ward = request.form.get("ward", "").strip()
    address_detail = request.form.get("address_detail", "").strip()

    note = request.form.get("note", "").strip()


    # =====================================================
    # HÌNH THỨC THANH TOÁN
    #
    # deposit = cọc
    # full    = thanh toán toàn bộ
    # =====================================================

    payment_type = request.form.get("payment_type", "deposit").strip()

    if payment_type not in ("deposit", "full"):
        payment_type = "deposit"


    # =====================================================
    # SỐ LƯỢNG
    # =====================================================

    try:
        quantity = int(request.form.get("quantity", 1))
    except (TypeError, ValueError):
        return "Số lượng không hợp lệ", 400

    if quantity < 1 or quantity > 2:
        return """
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <title>Số lượng không hợp lệ</title>
        </head>
        <body>
            <h2>Mỗi đơn chỉ được đặt tối đa 2 sản phẩm</h2>
            <p>Vui lòng chọn số lượng từ 1 đến 2.</p>
            <a href="/">Quay lại trang chủ</a>
        </body>
        </html>
        """, 400


    # =====================================================
    # DATABASE
    # =====================================================

    conn = get_db()
    cursor = conn.cursor()

    try:

        # =================================================
        # LẤY SẢN PHẨM
        # =================================================

        cursor.execute(
            """
            SELECT
                id,
                name,
                brand,
                price,
                deposit,
                eta,
                image_url,
                product_type,
                active
            FROM products
            WHERE id=%s
            AND active=TRUE
            LIMIT 1
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if product is None:
            return "Không tìm thấy sản phẩm", 404

        product_name = product[1]
        product_brand = product[2]
        product_price = product[3] or 0
        product_deposit = product[4] or 0


        # =================================================
        # SỐ TIỀN THANH TOÁN BAN ĐẦU
        # =================================================

        if payment_type == "full":
            payment_amount = product_price * quantity
        else:
            payment_amount = product_deposit * quantity

        requires_payment = payment_amount > 0


        # =================================================
        # CHỐNG TẠO NHIỀU ĐƠN PAYOS CHƯA THANH TOÁN
        #
        # Chỉ "Chưa thanh toán" mới khóa việc tạo đơn mới.
        #
        # Đơn cọc 0đ có trạng thái "Chờ xác nhận" nên khách
        # vẫn có thể tiếp tục đặt đơn khác.
        # =================================================

        order_token = request.cookies.get("order_token")
        existing_order = None


        # =================================================
        # KIỂM TRA ĐƠN CHƯA THANH TOÁN THEO COOKIE
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
                (order_token, "Chưa thanh toán")
            )

            candidate = cursor.fetchone()

            if candidate:

                expires_at = normalize_expires_at(candidate[2])

                if is_order_expired(expires_at):
                    mark_order_expired(
                        cursor,
                        conn,
                        candidate[0]
                    )
                else:
                    existing_order = candidate


        # =================================================
        # KIỂM TRA ĐƠN CHƯA THANH TOÁN THEO SĐT
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
                ORDER BY id DESC
                LIMIT 1
                """,
                (phone, "Chưa thanh toán")
            )

            candidate = cursor.fetchone()

            if candidate:

                expires_at = normalize_expires_at(candidate[2])

                if is_order_expired(expires_at):
                    mark_order_expired(
                        cursor,
                        conn,
                        candidate[0]
                    )
                else:
                    existing_order = candidate


        # =================================================
        # ĐÃ CÓ ĐƠN PAYOS CÒN HẠN
        #
        # Không tạo đơn mới.
        # Đưa khách trở lại link thanh toán của đơn cũ.
        # =================================================

        if existing_order:

            old_order_code = existing_order[0]
            old_payment_url = existing_order[1]
            old_token = existing_order[4]

            if old_payment_url:

                response = make_response(
                    redirect(old_payment_url)
                )

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

            return f"""
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8">
                <title>Đơn đang xử lý</title>
            </head>
            <body>
                <h2>Bạn đang có đơn chưa thanh toán</h2>
                <p>Mã đơn: <b>{old_order_code}</b></p>
                <a href="/order-status">Theo dõi đơn hàng</a>
            </body>
            </html>
            """, 400


        # =================================================
        # GIỮ / TRỪ TỒN KHO
        # =================================================

        stock_reserved = reserve_stock(
            cursor,
            product_id,
            quantity
        )

        if not stock_reserved:

            conn.rollback()

            return """
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8">
                <title>Không đủ hàng</title>
            </head>
            <body>
                <h2>Sản phẩm không còn đủ số lượng</h2>
                <p>Vui lòng chọn số lượng nhỏ hơn.</p>
                <a href="/">Quay lại trang chủ</a>
            </body>
            </html>
            """, 400


        # =================================================
        # TẠO MÃ ĐƠN
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
        # TOKEN THEO DÕI ĐƠN
        # =================================================

        new_order_token = secrets.token_urlsafe(32)


        # =================================================
        # THỜI GIAN TẠO ĐƠN
        # =================================================

        created_time = get_now_vn()
        created_at = created_time.strftime("%d/%m/%Y %H:%M:%S")


        # =================================================
        # TRẠNG THÁI + THỜI HẠN THANH TOÁN
        #
        # Có tiền phải thanh toán:
        # → Chưa thanh toán
        # → PayOS có hạn 15 phút
        #
        # Cọc 0đ:
        # → Chờ xác nhận
        # → Không tạo PayOS
        # =================================================

        if requires_payment:

            expires_time = created_time + timedelta(minutes=15)
            expires_at_db = expires_time.replace(tzinfo=None)
            order_status = "Chưa thanh toán"

        else:

            expires_time = None
            expires_at_db = None
            order_status = "Chờ xác nhận"


        # =================================================
        # TẠO ĐƠN TRONG DATABASE
        #
        # payment_url và payment_order_code ban đầu để NULL.
        # Nếu cần PayOS sẽ cập nhật sau khi tạo link.
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

                payment_type,
                status,

                created_at,
                expires_at,

                payment_url,
                payment_order_code,

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

                %s,%s,

                %s,%s,

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

                product_id,

                product_name,
                product_brand,

                product_price,
                product_deposit,

                payment_type,
                order_status,

                created_at,
                expires_at_db,

                None,
                None,

                new_order_token,
                True
            )
        )


        # =================================================
        # ĐƠN CỌC / THANH TOÁN = 0Đ
        #
        # Không cần PayOS.
        #
        # Đơn được lưu ngay và Telegram báo cho Admin.
        # =================================================

        if not requires_payment:

            conn.commit()

            send_new_order_notification(
                order_code=order_code,
                fullname=fullname,
                phone=phone,
                product_name=product_name,
                quantity=quantity,
                payment_type=payment_type,
                payment_amount=0,
                status="Chờ xác nhận"
            )

            response = make_response(
                redirect("/order-status")
            )

            response.set_cookie(
                "order_token",
                new_order_token,
                max_age=60 * 60 * 24 * 30,
                httponly=True,
                samesite="Lax",
                secure=True
            )

            return response


        # =================================================
        # TẠO MÃ GIAO DỊCH PAYOS BAN ĐẦU
        #
        # Mã này được lưu vào payment_order_code.
        # Webhook sẽ dùng nó để xác định chính xác đây là
        # giao dịch cọc / thanh toán full ban đầu.
        # =================================================

        payos_order_code = int(
            time.time_ns() // 1_000_000
        )

        base_url = request.url_root.rstrip("/")


        # =================================================
        # DỮ LIỆU PAYOS
        # =================================================

        payment_data = {
            "orderCode": payos_order_code,
            "amount": payment_amount,
            "description": order_code,
            "returnUrl": base_url + "/payment/success",
            "cancelUrl": base_url + "/payment/cancel",
            "expiredAt": int(expires_time.timestamp())
        }


        # =================================================
        # TẠO LINK THANH TOÁN PAYOS
        # =================================================

        payment_link = payos.payment_requests.create(
            payment_data
        )

        payment_url = payment_link.checkout_url


        # =================================================
        # LƯU THÔNG TIN PAYOS BAN ĐẦU
        #
        # payment_url:
        # → link thanh toán
        #
        # payment_order_code:
        # → mã giao dịch PayOS dùng để webhook nhận diện
        # =================================================

        cursor.execute(
            """
            UPDATE orders
            SET
                payment_url=%s,
                payment_order_code=%s
            WHERE order_code=%s
            """,
            (
                payment_url,
                payos_order_code,
                order_code
            )
        )

        conn.commit()


        # =================================================
        # KHÔNG GỬI TELEGRAM TẠI ĐÂY
        #
        # Với đơn có tiền, Telegram chỉ được gửi sau khi
        # webhook PayOS xác nhận thanh toán thành công.
        # =================================================


        # =================================================
        # CHUYỂN KHÁCH SANG PAYOS
        # =================================================

        response = make_response(
            redirect(payment_url)
        )

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
        raise


    finally:

        cursor.close()
        conn.close()
