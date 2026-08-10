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
    # submit_order.py gửi:
    #
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
                payment_type,
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
        # KHÔNG TÌM THẤY ĐƠN
        # =================================================

        if order is None:

            print(
                "KHONG TIM THAY DON:",
                order_code
            )

            return "OK", 200


        order_id = order[0]

        current_status = order[1]

        payment_type = order[2]

        stock_reserved = order[3]

        product_id = order[4]

        quantity = order[5]


        print(
            "ORDER ID:",
            order_id
        )


        print(
            "CURRENT STATUS:",
            current_status
        )


        print(
            "PAYMENT TYPE:",
            payment_type
        )


        print(
            "STOCK RESERVED:",
            stock_reserved
        )


        # =================================================
        # ĐƠN ĐÃ ĐƯỢC THANH TOÁN TRƯỚC ĐÓ
        # =================================================

        if current_status in (
            "Đã cọc",
            "Đã chuyển khoản full"
        ):

            print(
                "DON DA THANH TOAN TRUOC DO"
            )

            return "OK", 200


        # =================================================
        # ĐƠN ĐÃ HỦY
        # =================================================

        if current_status == "Đã hủy":

            print(
                "DON DA BI HUY"
            )

            return "OK", 200


        # =================================================
        # ĐƠN ĐÃ HẾT HẠN
        # =================================================

        if current_status == "Hết hạn thanh toán":

            print(
                "DON DA HET HAN"
            )

            return "OK", 200


        # =================================================
        # CHỈ XỬ LÝ ĐƠN CHƯA THANH TOÁN
        # =================================================

        if current_status != "Chưa thanh toán":

            print(
                "TRANG THAI KHONG HOP LE:",
                current_status
            )

            return "OK", 200


        # =================================================
        # XÁC ĐỊNH TRẠNG THÁI SAU THANH TOÁN
        # =================================================

        if payment_type == "full":

            new_status = (
                "Đã chuyển khoản full"
            )

        else:

            new_status = (
                "Đã cọc"
            )


        print(
            "NEW STATUS:",
            new_status
        )


        # =================================================
        # THANH TOÁN THÀNH CÔNG
        #
        # Hàng đã được trừ khi tạo đơn.
        #
        # Vì vậy:
        #
        # - KHÔNG trừ kho thêm
        # - KHÔNG cộng kho lại
        #
        # Chỉ:
        #
        # - đổi trạng thái
        # - stock_reserved = FALSE
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
                new_status,
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


        print(
            "FINAL STATUS:",
            new_status
        )


        return "OK", 200


    except Exception:

        conn.rollback()

        raise


    finally:

        cursor.close()

        conn.close()
