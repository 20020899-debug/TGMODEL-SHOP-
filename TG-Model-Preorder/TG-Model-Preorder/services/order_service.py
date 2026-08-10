from datetime import datetime
from zoneinfo import ZoneInfo


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
    # DB đang lưu TIMESTAMP không timezone
    # nhưng quy ước giá trị là giờ Việt Nam
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


    now_vn = get_now_vn()


    return (
        expires_at <= now_vn
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
# TỰ ĐỘNG CHUYỂN ĐƠN HẾT HẠN
# =========================================================

def mark_order_expired(
    cursor,
    conn,
    order_code
):

    cursor.execute(
        """
        UPDATE orders

        SET status=%s

        WHERE order_code=%s
        AND status=%s
        """,
        (
            "Hết hạn thanh toán",
            order_code,
            "Chưa thanh toán"
        )
    )


    conn.commit()