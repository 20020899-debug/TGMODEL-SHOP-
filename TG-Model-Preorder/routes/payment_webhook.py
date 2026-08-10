from flask import (
    Blueprint,
    request
)

from database import get_db


payment_webhook_bp = Blueprint(
    "payment_webhook",
    __name__
)


# =========================================================
# WEBHOOK PAYOS
# =========================================================

@payment_webhook_bp.route(
    "/payment/webhook",
    methods=["POST"]
)
def webhook():

    print(
        "========== PAYOS WEBHOOK =========="
    )


    # =====================================================
    # LẤY DỮ LIỆU PAYOS
    # =====================================================

    data = request.get_json(
        silent=True
    )


    print(
        "PAYOS DATA:",
        data
    )


    if not data:

        return "NO DATA", 400


    # =====================================================
    # PAYOS KHÔNG BÁO THÀNH CÔNG
    # =====================================================

    if data.get("code") != "00":

        print(
            "PAYMENT NOT SUCCESS"
        )

        return "OK", 200


    # =====================================================
    # LẤY ORDER CODE
    #
    # submit_order.py đang gửi:
    # description = TGMxxx
    # =====================================================

    order_code = (
        data
        .get("data", {})
        .get("description")
    )


    if not order_code:

        print(
            "KHONG CO ORDER CODE"
        )

        return "OK", 200


    print(
        "ORDER CODE:",
        order_code
    )


    # =====================================================
    # DATABASE
    # =====================================================

    conn = get_db()
    cursor = conn.cursor()


    try:

        # =================================================
        # TÌM ĐƠN
        # =================================================

        cursor.execute(
            """
            SELECT
                id,
                status,
                stock_reserved,
                product_id,
                quantity

            FROM orders

            WHERE order_code=%s

            LIMIT 1
            """,
            (
                order_code,
            )
        )


        order = cursor.fetchone()


        # =================================================
        # KHÔNG TÌM THẤY
        # =================================================

        if order is None:

            print(
                "KHONG TIM THAY DON:",
                order_code
            )

            return "OK", 200


        order_id = order[0]
        current_status = order[1]
        stock_reserved = order[2]
        product_id = order[3]
        quantity = order[4]


        print(
            "ORDER ID:",
            order_id
        )


        print(
            "CURRENT STATUS:",
            current_status
        )


        print(
            "STOCK RESERVED:",
            stock_reserved
        )


        # =================================================
        # ĐÃ CỌC TRƯỚC ĐÓ
        # =================================================

        if current_status == "Đã cọc":

            print(
                "DON DA COC TRUOC DO"
            )

            return "OK", 200


        # =================================================
        # ĐÃ HỦY
        # =================================================

        if current_status == "Đã hủy":

            print(
                "DON DA BI HUY"
            )

            return "OK", 200


        # =================================================
        # HẾT HẠN
        # =================================================

        if current_status == "Hết hạn thanh toán":

            print(
                "DON DA HET HAN"
            )

            return "OK", 200


        # =================================================
        # CHỈ XÁC NHẬN ĐƠN CHƯA THANH TOÁN
        # =================================================

        if current_status != "Chưa thanh toán":

            print(
                "TRANG THAI KHONG HOP LE:",
                current_status
            )

            return "OK", 200


        # =================================================
        # THANH TOÁN THÀNH CÔNG
        #
        # QUAN TRỌNG:
        #
        # Hàng đã được trừ ngay khi tạo đơn.
        #
        # Vì vậy:
        #
        # - KHÔNG trừ kho thêm
        # - KHÔNG cộng kho lại
        #
        # Chỉ bỏ trạng thái "đang giữ hàng"
        # =================================================

        cursor.execute(
            """
            UPDATE orders

            SET
                status=%s,
                stock_reserved=FALSE

            WHERE id=%s
            AND status=%s
            """,
            (
                "Đã cọc",
                order_id,
                "Chưa thanh toán"
            )
        )


        updated_rows = (
            cursor.rowcount
        )


        conn.commit()


        print(
            "PAYMENT UPDATED ROW:",
            updated_rows
        )


        print(
            "PAYMENT SUCCESS:",
            order_code
        )


        return "OK", 200


    except Exception:

        conn.rollback()

        raise


    finally:

        cursor.close()

        conn.close()
