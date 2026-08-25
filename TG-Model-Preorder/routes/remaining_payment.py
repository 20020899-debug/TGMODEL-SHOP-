from flask import Blueprint, request, redirect

from datetime import timedelta
import time

from psycopg2.extras import RealDictCursor

from database import get_db
from payos_service import payos

from services.order_service import (
    get_now_vn,
    normalize_expires_at,
    is_order_expired
)


remaining_payment_bp = Blueprint("remaining_payment", __name__)


# =========================================================
# THANH TOÁN PHẦN CÒN LẠI CỦA PRE-ORDER
#
# Chỉ áp dụng khi:
# - đơn sử dụng hình thức cọc
# - trạng thái = "Chờ thanh toán phần còn lại"
#
# Nếu link PayOS cũ còn hạn:
# → sử dụng lại link cũ.
#
# Nếu link PayOS cũ hết hạn:
# → tạo link mới.
#
# Link hết hạn KHÔNG hủy đơn và KHÔNG hoàn kho.
# =========================================================

@remaining_payment_bp.route(
    "/order/<int:order_id>/pay-remaining",
    methods=["POST"]
)
def pay_remaining(order_id):

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:

        # =================================================
        # KHÓA VÀ LẤY ĐƠN
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM orders
            WHERE id=%s
            LIMIT 1
            FOR UPDATE
            """,
            (order_id,)
        )

        order = cursor.fetchone()

        if order is None:
            return "Không tìm thấy đơn hàng", 404


        # =================================================
        # KIỂM TRA HÌNH THỨC THANH TOÁN
        # =================================================

        if order["payment_type"] != "deposit":
            return "Đơn hàng này không sử dụng hình thức đặt cọc", 400


        # =================================================
        # KIỂM TRA TRẠNG THÁI
        #
        # Admin phải chuyển đơn sang:
        # "Chờ thanh toán phần còn lại"
        #
        # thì khách mới được phép thanh toán.
        # =================================================

        if order["status"] != "Chờ thanh toán phần còn lại":
            return "Đơn hàng chưa được phép thanh toán phần còn lại", 400


        # =================================================
        # TÍNH SỐ TIỀN CÒN LẠI
        #
        # Tổng đơn = Giá × Số lượng
        # Đã cọc   = Tiền cọc × Số lượng
        # Còn lại  = Tổng đơn - Đã cọc
        # =================================================

        quantity = order["quantity"] or 1
        price = order["price"] or 0
        deposit = order["deposit"] or 0

        total_amount = price * quantity
        deposited_amount = deposit * quantity
        remaining_amount = max(total_amount - deposited_amount, 0)


        # =================================================
        # KHÔNG CÒN TIỀN PHẢI THANH TOÁN
        # =================================================

        if remaining_amount <= 0:
            return "Đơn hàng không còn số tiền cần thanh toán", 400


        # =================================================
        # KIỂM TRA LINK PAYOS CŨ
        #
        # Nếu link cũ vẫn còn hạn:
        # → chuyển thẳng sang link đó.
        #
        # Tránh tạo nhiều giao dịch PayOS cho cùng một đơn.
        # =================================================

        old_payment_url = order["remaining_payment_url"]

        old_expires_at = normalize_expires_at(
            order["remaining_expires_at"]
        )

        if (
            old_payment_url
            and old_expires_at
            and not is_order_expired(old_expires_at)
        ):
            return redirect(old_payment_url)


        # =================================================
        # TẠO HẠN THANH TOÁN MỚI
        #
        # Link thanh toán phần còn lại có hiệu lực 15 phút.
        #
        # Khi hết hạn khách có thể bấm lại để tạo link mới.
        # =================================================

        created_time = get_now_vn()
        expires_time = created_time + timedelta(minutes=15)

        expires_at_db = expires_time.replace(tzinfo=None)


        # =================================================
        # MÃ GIAO DỊCH PAYOS
        #
        # Đây là orderCode riêng của PayOS,
        # không phải mã đơn TGMxxx của website.
        # =================================================

        payos_order_code = int(
            time.time_ns() // 1_000_000
        )


        # =================================================
        # DOMAIN WEBSITE
        # =================================================

        base_url = request.url_root.rstrip("/")


        # =================================================
        # DỮ LIỆU PAYOS
        #
        # Description:
        #
        # TGM001-REM
        #
        # "-REM" giúp webhook nhận biết đây là thanh toán
        # phần còn lại của Pre-order.
        # =================================================

        payment_data = {
            "orderCode": payos_order_code,
            "amount": remaining_amount,
            "description": f"{order['order_code']}-REM",
            "returnUrl": base_url + "/payment/success",
            "cancelUrl": base_url + "/payment/cancel",
            "expiredAt": int(expires_time.timestamp())
        }


        # =================================================
        # TẠO LINK PAYOS
        # =================================================

        payment_link = payos.payment_requests.create(
            payment_data
        )

        payment_url = payment_link.checkout_url


        # =================================================
        # LƯU LINK THANH TOÁN PHẦN CÒN LẠI
        #
        # Không sử dụng payment_url ban đầu.
        #
        # Hai loại link được lưu riêng:
        #
        # payment_url           = thanh toán ban đầu
        # remaining_payment_url = thanh toán phần còn lại
        # =================================================

        cursor.execute(
            """
            UPDATE orders

            SET
                remaining_payment_url=%s,
                remaining_expires_at=%s

            WHERE id=%s
            """,
            (
                payment_url,
                expires_at_db,
                order_id
            )
        )

        conn.commit()


        # =================================================
        # CHUYỂN KHÁCH SANG PAYOS
        # =================================================

        return redirect(payment_url)


    except Exception:

        conn.rollback()
        raise


    finally:

        cursor.close()
        conn.close()
