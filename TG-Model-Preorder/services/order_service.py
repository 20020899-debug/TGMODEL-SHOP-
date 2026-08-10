from datetime import datetime
from zoneinfo import ZoneInfo
from collections.abc import Mapping

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
#
# Database đang lưu giờ Việt Nam
# dưới dạng TIMESTAMP không timezone.
# =========================================================

def normalize_expires_at(
    expires_at
):

    if expires_at is None:

        return None


    # =====================================================
    # TIMESTAMP KHÔNG CÓ TIMEZONE
    # → coi là giờ Việt Nam
    # =====================================================

    if expires_at.tzinfo is None:

        expires_at = expires_at.replace(
            tzinfo=VIETNAM_TZ
        )


    # =====================================================
    # ĐÃ CÓ TIMEZONE
    # → đổi sang giờ Việt Nam
    # =====================================================

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


    # =====================================================
    # KHÔNG CÓ THỜI GIAN HẾT HẠN
    # → coi như đã hết hạn
    # =====================================================

    if expires_at is None:

        return True


    return (
        expires_at
        <=
        get_now_vn()
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
# LẤY GIÁ TRỊ TỪ DATABASE ROW
#
# Hỗ trợ:
#
# cursor thường:
# tuple
#
# RealDictCursor:
# RealDictRow
# =========================================================

def get_row_value(
    row,
    key,
    index
):

    if isinstance(
        row,
        Mapping
    ):

        return row.get(
            key
        )


    return row[index]


# =========================================================
# CHUYỂN ĐƠN THÀNH HẾT HẠN
#
# Đồng thời hoàn tồn kho nếu đơn đang giữ hàng.
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
    # ĐỌC DỮ LIỆU
    #
    # Hỗ trợ cả tuple và RealDictRow
    # =====================================================

    product_id = get_row_value(
        order,
        "product_id",
        0
    )


    quantity = get_row_value(
        order,
        "quantity",
        1
    )


    stock_reserved = get_row_value(
        order,
        "stock_reserved",
        2
    )


    status = get_row_value(
        order,
        "status",
        3
    )


    # =====================================================
    # CHỈ XỬ LÝ ĐƠN CHƯA THANH TOÁN
    # =====================================================

    if status != "Chưa thanh toán":

        return False


    # =====================================================
    # NẾU ĐƠN ĐANG GIỮ HÀNG
    # → HOÀN HÀNG VỀ KHO
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
                + str(
                    order_code
                )
            )


    # =====================================================
    # ĐỔI TRẠNG THÁI
    # + BỎ GIỮ HÀNG
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
    # COMMIT
    # =====================================================

    conn.commit()


    return True
