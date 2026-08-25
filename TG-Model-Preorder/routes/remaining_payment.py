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


remaining_payment_bp = Blueprint(
    "remaining_payment",
    __name__
)


# =========================================================
# THANH TOÁN PHẦN CÒN LẠI CỦA PRE-ORDER
#
# Chỉ áp dụng khi:
# - đơn chọn hình thức cọc
# - trạng thái = "Chờ thanh toán phần còn lại"
#
# Nếu link PayOS cũ còn hạn:
# → sử dụng lại link cũ.
#
# Nếu link cũ hết hạn:
# → tạo link PayOS mới.
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
        # KIỂM TRA ĐÚNG ĐƠN CỌC
        # =================================================

        if order["payment_type"] != "deposit":
            return "Đơn hàng này không sử dụng hình thức đặt cọc", 400


        # =================================================
        # KIỂM TRA TRẠNG THÁI
        #
        # Admin phải chuyển đơn sang trạng thái này trước
        # thì khách mới được thanh toán phần còn lại.
        # =================================================

        if order["status"] != "Chờ thanh toán phần còn lại":
            return "Đơn hàng chưa được phép thanh toán phần còn lại", 400


        # =================================================
        # TÍNH SỐ TIỀN CÒN LẠI
        # =================================================

        quantity = order["quantity"] or 1
        price = order["price"] or 0
        deposit = order["deposit"] or 0

        total_amount = price * quantity
        deposited_amount = deposit * quantity

        remaining_amount = max(
            total_amount - deposited_amount,
            0
        )


        # =================================================
        # KHÔNG CÒN TIỀN PHẢI THANH TOÁN
        # =================================================

        if remaining_amount <= 0:
            return "Đơn hàng không còn số tiền cần thanh toán", 400


        # =================================================
        # KIỂM TRA LINK PAYOS CŨ
        #
        # Nếu link cũ vẫn còn hạn thì không tạo thêm link.
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
        # =================================================

        created_time = get_now_vn()

        expires_time = created_time + timedelta(
            minutes=15
        )

        expires_at_db = expires_time.replace(
            tzinfo=None
        )


        # =================================================
        # MÃ GIAO DỊCH PAYOS
        #
        # Dùng timestamp mili-giây để hạn chế trùng mã.
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
        # Prefix "REM-" giúp webhook phân biệt đây là
        # thanh toán phần còn lại, không phải tiền cọc.
        # =================================================

        payment_data = {
            "orderCode": payos_order_code,
            "amount": remaining_amount,
            "description": f"REM-{order['order_code']}",
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
