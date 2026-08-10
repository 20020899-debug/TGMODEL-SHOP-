# =========================================================
# LẤY TỒN KHO HIỆN TẠI
# =========================================================

def get_stock(
    cursor,
    product_id
):

    cursor.execute(
        """
        SELECT stock

        FROM product_stock

        WHERE product_id=%s
        """,
        (
            product_id,
        )
    )


    row = cursor.fetchone()


    if row is None:

        return 0


    return int(
        row[0]
    )


# =========================================================
# KIỂM TRA CÒN ĐỦ HÀNG KHÔNG
# =========================================================

def has_enough_stock(
    cursor,
    product_id,
    quantity
):

    if quantity <= 0:

        return False


    stock = get_stock(
        cursor,
        product_id
    )


    return stock >= quantity


# =========================================================
# GIỮ / TRỪ TỒN KHO
#
# Dùng khi khách tạo đơn.
# =========================================================

def reserve_stock(
    cursor,
    product_id,
    quantity
):

    if quantity <= 0:

        return False


    # =====================================================
    # UPDATE trực tiếp để chống 2 khách đặt cùng lúc.
    #
    # Chỉ trừ nếu stock vẫn >= quantity.
    # =====================================================

    cursor.execute(
        """
        UPDATE product_stock

        SET stock =
            stock - %s

        WHERE product_id=%s

        AND stock >= %s
        """,
        (
            quantity,
            product_id,
            quantity
        )
    )


    return (
        cursor.rowcount == 1
    )


# =========================================================
# TRẢ HÀNG VỀ KHO
#
# Dùng khi:
#
# - Đơn bị hủy
# - Đơn hết hạn thanh toán
# =========================================================

def release_stock(
    cursor,
    product_id,
    quantity
):

    if quantity <= 0:

        return False


    cursor.execute(
        """
        UPDATE product_stock

        SET stock =
            stock + %s

        WHERE product_id=%s
        """,
        (
            quantity,
            product_id
        )
    )


    return (
        cursor.rowcount == 1
    )


# =========================================================
# ĐẶT TỒN KHO THỦ CÔNG
#
# Sau này admin có thể dùng hàm này.
# =========================================================

def set_stock(
    cursor,
    product_id,
    stock
):

    if stock < 0:

        stock = 0


    cursor.execute(
        """
        INSERT INTO product_stock
        (
            product_id,
            stock
        )

        VALUES
        (
            %s,
            %s
        )

        ON CONFLICT (product_id)

        DO UPDATE SET
            stock = EXCLUDED.stock
        """,
        (
            product_id,
            stock
        )
    )