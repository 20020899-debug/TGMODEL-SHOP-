from flask import Blueprint, request

from database import get_db
from payos_service import payos

from services.notification_service import (
    send_new_order_notification
)


payment_webhook_bp = Blueprint(
    "payment_webhook",
    __name__
)


# =========================================================
# WEBHOOK PAYOS
#
# Xử lý 2 loại thanh toán:
#
# 1. Thanh toán ban đầu
#    - Cọc
#    - Chuyển khoản full
#
# 2. Thanh toán phần còn lại của Pre-order
#
# Webhook có thể được PayOS gửi lại nhiều lần nên việc
# kiểm tra trạng thái và mã giao dịch giúp tránh xử lý
# trùng một giao dịch đã hoàn thành.
# =========================================================

@payment_webhook_bp.route(
    "/payment/webhook",
    methods=["POST"]
)
def webhook():

    print("========== PAYOS WEBHOOK ==========")


    try:

        # =================================================
        # XÁC MINH WEBHOOK
        # =================================================

        webhook_data = payos.webhooks.verify(
            request.data
        )

        print(
            "WEBHOOK VERIFIED:",
            webhook_data
        )


        # =================================================
        # THÔNG TIN GIAO DỊCH PAYOS
        # =================================================

        description = (
            webhook_data.description
            or ""
        ).strip()

        paid_amount = (
            webhook_data.amount
            or 0
        )

        payos_order_code = (
            webhook_data.order_code
        )


        print(
            "DESCRIPTION:",
            description
        )

        print(
            "PAYOS ORDER CODE:",
            payos_order_code
        )

        print(
            "PAID AMOUNT:",
            paid_amount
        )


        if not payos_order_code:

            print(
                "WEBHOOK KHONG CO PAYOS ORDER CODE"
            )

            return "OK", 200


        # =================================================
        # DATABASE
        # =================================================

        conn = get_db()
        cursor = conn.cursor()


        try:

            # =================================================
            # TÌM ĐƠN THEO MÃ GIAO DỊCH PAYOS
            #
            # Không chỉ dựa vào description vì cùng một đơn
            # có thể thanh toán PayOS hai lần:
            #
            # - lần đầu
            # - phần còn lại
            # =================================================

            cursor.execute(
                """
                SELECT
                    id,
                    status,
                    payment_type,
                    quantity,

                    order_code,
                    fullname,
                    phone,
                    product_name,

                    price,
                    deposit,

                    payment_order_code,
                    remaining_payment_order_code

                FROM orders

                WHERE
                    payment_order_code=%s
                    OR
                    remaining_payment_order_code=%s

                LIMIT 1

                FOR UPDATE
                """,
                (
                    payos_order_code,
                    payos_order_code
                )
            )


            order = cursor.fetchone()


            # =================================================
            # TƯƠNG THÍCH ĐƠN CŨ
            #
            # Các đơn được tạo trước khi có cột
            # payment_order_code chưa lưu mã giao dịch PayOS.
            #
            # Với các đơn này mới thử tìm bằng description.
            # =================================================

            if order is None and description:

                cursor.execute(
                    """
                    SELECT
                        id,
                        status,
                        payment_type,
                        quantity,

                        order_code,
                        fullname,
                        phone,
                        product_name,

                        price,
                        deposit,

                        payment_order_code,
                        remaining_payment_order_code

                    FROM orders

                    WHERE order_code=%s

                    LIMIT 1

                    FOR UPDATE
                    """,
                    (
                        description,
                    )
                )

                order = cursor.fetchone()


            # =================================================
            # KHÔNG TÌM THẤY ĐƠN
            # =================================================

            if order is None:

                print(
                    "KHONG TIM THAY DON CHO PAYOS:",
                    payos_order_code
                )

                return "OK", 200


            # =================================================
            # DỮ LIỆU ĐƠN
            # =================================================

            order_id = order[0]
            current_status = order[1]
            payment_type = order[2]
            quantity = order[3] or 1

            order_code = order[4]
            fullname = order[5] or ""
            phone = order[6] or ""
            product_name = order[7] or ""

            price = order[8] or 0
            deposit = order[9] or 0

            payment_order_code = order[10]
            remaining_payment_order_code = order[11]


            print(
                "ORDER:",
                order_code
            )

            print(
                "CURRENT STATUS:",
                current_status
            )


            # =================================================
            # XÁC ĐỊNH LOẠI THANH TOÁN
            #
            # Ưu tiên xác định bằng mã PayOS đã lưu trong DB.
            # =================================================

            is_initial_payment = (
                payment_order_code == payos_order_code
            )

            is_remaining_payment = (
                remaining_payment_order_code
                == payos_order_code
            )


            # =================================================
            # TƯƠNG THÍCH ĐƠN CŨ
            #
            # Đơn cũ chưa có payment_order_code nhưng đang
            # "Chưa thanh toán" được coi là thanh toán lần đầu.
            # =================================================

            if (
                not is_initial_payment
                and not is_remaining_payment
                and current_status == "Chưa thanh toán"
                and description == order_code
            ):
                is_initial_payment = True


            # =================================================
            # THANH TOÁN LẦN ĐẦU
            # =================================================

            if is_initial_payment:

                # =============================================
                # CHỐNG XỬ LÝ WEBHOOK TRÙNG
                # =============================================

                if current_status != "Chưa thanh toán":

                    print(
                        "BO QUA WEBHOOK LAN DAU - STATUS:",
                        current_status
                    )

                    return "OK", 200


                # =============================================
                # TÍNH SỐ TIỀN PHẢI THANH TOÁN
                # =============================================

                if payment_type == "full":

                    expected_amount = (
                        price
                        * quantity
                    )

                    new_status = (
                        "Đã chuyển khoản full"
                    )

                else:

                    expected_amount = (
                        deposit
                        * quantity
                    )

                    new_status = (
                        "Đã cọc"
                    )


                print(
                    "PAYMENT TYPE: INITIAL"
                )

                print(
                    "EXPECTED AMOUNT:",
                    expected_amount
                )


                # =============================================
                # KIỂM TRA SỐ TIỀN
                # =============================================

                if paid_amount < expected_amount:

                    print(
                        "THANH TOAN LAN DAU KHONG DU TIEN"
                    )

                    return "OK", 200


                # =============================================
                # CẬP NHẬT ĐƠN
                # =============================================

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

                updated_rows = cursor.rowcount

                conn.commit()


                # =============================================
                # TELEGRAM
                # =============================================

                if updated_rows > 0:

                    telegram_result = (
                        send_new_order_notification(
                            order_code=order_code,
                            fullname=fullname,
                            phone=phone,
                            product_name=product_name,
                            quantity=quantity,
                            payment_type=payment_type,
                            payment_amount=expected_amount,
                            status=new_status
                        )
                    )

                    print(
                        "TELEGRAM RESULT:",
                        telegram_result
                    )


                print(
                    "INITIAL PAYMENT SUCCESS:",
                    order_code
                )

                print(
                    "FINAL STATUS:",
                    new_status
                )


                return "OK", 200


            # =================================================
            # THANH TOÁN PHẦN CÒN LẠI
            # =================================================

            if is_remaining_payment:

                # =============================================
                # CHỈ CHẤP NHẬN KHI ADMIN ĐÃ YÊU CẦU
                # THANH TOÁN PHẦN CÒN LẠI
                # =============================================

                if (
                    current_status
                    != "Chờ thanh toán phần còn lại"
                ):

                    print(
                        "BO QUA REMAINING PAYMENT - STATUS:",
                        current_status
                    )

                    return "OK", 200


                # =============================================
                # TÍNH SỐ TIỀN CÒN LẠI
                #
                # Tổng đơn:
                # price × quantity
                #
                # Đã cọc:
                # deposit × quantity
                # =============================================

                total_amount = (
                    price
                    * quantity
                )

                deposited_amount = (
                    deposit
                    * quantity
                )

                expected_amount = max(
                    total_amount
                    - deposited_amount,
                    0
                )


                print(
                    "PAYMENT TYPE: REMAINING"
                )

                print(
                    "TOTAL AMOUNT:",
                    total_amount
                )

                print(
                    "DEPOSITED AMOUNT:",
                    deposited_amount
                )

                print(
                    "EXPECTED REMAINING:",
                    expected_amount
                )


                # =============================================
                # KHÔNG CÒN TIỀN PHẢI THANH TOÁN
                # =============================================

                if expected_amount <= 0:

                    print(
                        "DON KHONG CON SO TIEN PHAI THANH TOAN"
                    )

                    return "OK", 200


                # =============================================
                # KIỂM TRA SỐ TIỀN
                # =============================================

                if paid_amount < expected_amount:

                    print(
                        "THANH TOAN PHAN CON LAI KHONG DU TIEN"
                    )

                    return "OK", 200


                # =============================================
                # CẬP NHẬT ĐÃ THANH TOÁN ĐỦ
                #
                # Không tác động tồn kho vì hàng của đơn này
                # đã được trừ từ khi khách tạo đơn ban đầu.
                # =============================================

                cursor.execute(
                    """
                    UPDATE orders

                    SET
                        status=%s,
                        remaining_payment_url=NULL,
                        remaining_expires_at=NULL

                    WHERE id=%s
                    AND status=%s
                    """,
                    (
                        "Đã thanh toán đủ",
                        order_id,
                        "Chờ thanh toán phần còn lại"
                    )
                )

                updated_rows = cursor.rowcount

                conn.commit()


                # =============================================
                # TELEGRAM
                #
                # Báo Admin khi khách đã thanh toán phần
                # còn lại của đơn Pre-order.
                # =============================================

                if updated_rows > 0:

                    telegram_result = (
                        send_new_order_notification(
                            order_code=order_code,
                            fullname=fullname,
                            phone=phone,
                            product_name=product_name,
                            quantity=quantity,
                            payment_type="remaining",
                            payment_amount=expected_amount,
                            status="Đã thanh toán đủ"
                        )
                    )

                    print(
                        "TELEGRAM RESULT:",
                        telegram_result
                    )


                print(
                    "REMAINING PAYMENT SUCCESS:",
                    order_code
                )

                print(
                    "FINAL STATUS: Đã thanh toán đủ"
                )


                return "OK", 200


            # =================================================
            # KHÔNG XÁC ĐỊNH ĐƯỢC GIAO DỊCH
            # =================================================

            print(
                "KHONG XAC DINH DUOC LOAI THANH TOAN:",
                payos_order_code
            )

            return "OK", 200


        except Exception as error:

            conn.rollback()

            print(
                "DATABASE WEBHOOK ERROR:",
                error
            )

            raise


        finally:

            cursor.close()
            conn.close()


    except Exception as error:

        print(
            "INVALID PAYOS WEBHOOK:",
            error
        )

        return "INVALID WEBHOOK", 400
