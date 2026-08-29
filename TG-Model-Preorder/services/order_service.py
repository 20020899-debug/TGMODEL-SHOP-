from datetime import datetime
from zoneinfo import ZoneInfo

from services.stock_service import (
    release_stock
)


# =========================================================
# MÚI GIỜ VIỆT NAM
# =========================================================

VIETNAM_TZ = ZoneInfo(
    "Asia/Ho_Chi_Minh"
)


# =========================================================
# LẤY THỜI GIAN HIỆN TẠI Ở VIỆT NAM
# =========================================================

def get_now_vn():

    return datetime.now(
        VIETNAM_TZ
    )


# =========================================================
# CHUẨN HÓA EXPIRES_AT
# =========================================================

def normalize_expires_at(
    expires_at
):

    if expires_at is None:

        return None


    # =====================================================
    # Database lưu giờ Việt Nam nhưng không timezone
    # =====================================================

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
# KIỂM TRA ĐƠN ĐÃ HẾT HẠN CHƯA
# =========================================================

def is_order_expired(
    expires_at
):

    expires_at = normalize_expires_at(
        expires_at
    )


    if expires_at is None:

        return True


    return (
        expires_at <= get_now_vn()
    )


# =========================================================
# CHUYỂN EXPIRES_AT SANG UNIX TIMESTAMP
# =========================================================

def expires_to_timestamp(
    expires_at
):

    expires_at = normalize_expires_at(
        expires_at
    )


    if expires_at is None:

        return None


    return int(
        expires_at.timestamp()
    )


# =========================================================
# CHUYỂN ĐƠN THÀNH HẾT HẠN
#
# Đồng thời hoàn tồn kho nếu đơn đang giữ hàng.
#
# Hàm này hỗ trợ cả:
#
# - cursor thường
# - RealDictCursor
#
# để tránh lỗi khi được gọi từ các route khác nhau.
# =========================================================

def mark_order_expired(
    cursor,
    conn,
    order_code
):

    # =====================================================
    # LẤY THÔNG TIN ĐƠN
    # =====================================================

    cursor.execute(
        """
        SELECT
            product_id,
            quantity,
            stock_reserved,
            status

        FROM orders

        WHERE order_code=%s

        LIMIT 1
        """,
        (
            order_code,
        )
    )


    order = cursor.fetchone()


    # =====================================================
    # KHÔNG TÌM THẤY ĐƠN
    # =====================================================

    if order is None:

        return False


    # =====================================================
    # HỖ TRỢ REALDICTCURSOR VÀ CURSOR THƯỜNG
    #
    # RealDictCursor:
    #
    # order["product_id"]
    #
    # Cursor thường:
    #
    # order[0]
    # =====================================================

    if isinstance(
        order,
        dict
    ):

        product_id = order[
            "product_id"
        ]

        quantity = order[
            "quantity"
        ]

        stock_reserved = order[
            "stock_reserved"
        ]

        status = order[
            "status"
        ]

    else:

        product_id = order[0]

        quantity = order[1]

        stock_reserved = order[2]

        status = order[3]


    # =====================================================
    # CHỈ XỬ LÝ ĐƠN CHƯA THANH TOÁN
    # =====================================================

    if status != "Chưa thanh toán":

        return False


    # =====================================================
    # NẾU ĐANG GIỮ HÀNG
    # → TRẢ HÀNG VỀ KHO
    # =====================================================

    if (
        stock_reserved
        and
        product_id is not None
        and
        quantity is not None
        and
        quantity > 0
    ):

        released = release_stock(
            cursor,
            product_id,
            quantity
        )


        if not released:

            raise RuntimeError(
                "Không thể hoàn tồn kho cho đơn "
                + str(order_code)
            )


    # =====================================================
    # ĐỔI TRẠNG THÁI
    #
    # Chưa thanh toán
    #       ↓
    # Hết hạn thanh toán
    #
    # Đồng thời:
    #
    # stock_reserved = FALSE
    #
    # để đảm bảo lần sau không hoàn kho lần nữa.
    # =====================================================

    cursor.execute(
        """
        UPDATE orders

        SET
            status=%s,
            stock_reserved=FALSE

        WHERE order_code=%s
        AND status=%s
        """,
        (
            "Hết hạn thanh toán",
            order_code,
            "Chưa thanh toán"
        )
    )


    # =====================================================
    # KIỂM TRA CÓ UPDATE THẬT KHÔNG
    # =====================================================

    updated_rows = cursor.rowcount


    # =====================================================
    # COMMIT
    # =====================================================

    conn.commit()


    return (
        updated_rows > 0
    )
