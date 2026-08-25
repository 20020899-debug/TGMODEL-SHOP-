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
# 1. TGM001
#    → thanh toán ban đầu
#    → cọc hoặc thanh toán full
#
# 2. REM-TGM001
#    → thanh toán phần còn lại của Pre-order
# =========================================================

@payment_webhook_bp.route(
    "/payment/webhook",
    methods=["POST"]
)
def webhook():

    print("========== PAYOS WEBHOOK ==========")


    try:

        # =================================================
        # XÁC MINH WEBHOOK PAYOS
        # =================================================

        webhook_data = payos.webhooks.verify(
            request.data
        )

        print(
            "WEBHOOK VERIFIED:",
            webhook_data
        )


        # =================================================
        # THÔNG TIN THANH TOÁN
        # =================================================

        description = (
            webhook_data.description
            or ""
        ).strip()

        paid_amount = webhook_data.amount or 0

        print("DESCRIPTION:", description)
        print("PAID AMOUNT:", paid_amount)


        if not description:
            return "OK", 200


        # =================================================
        # XÁC ĐỊNH LOẠI THANH TOÁN
        #
        # REM- = thanh toán phần còn lại.
        # Không có REM- = thanh toán ban đầu.
        # =================================================

        is_remaining_payment = description.startswith(
            "REM-"
        )


        if is_remaining_payment:
            order_code = description[4:]
        else:
            order_code = description


        if not order_code:
            return "OK", 200


        print("ORDER CODE:", order_code)

        print(
            "PAYMENT TYPE:",
            (
                "REMAINING"
                if is_remaining_payment
                else "INITIAL"
            )
        )


        # =================================================
        # DATABASE
        # =================================================

        conn = get_db()
        cursor = conn.cursor()


        try:

            # =================================================
            # KHÓA VÀ LẤY ĐƠN
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
                    deposit

                FROM orders

                WHERE order_code=%s

                LIMIT 1
                FOR UPDATE
                """,
                (order_code,)
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
            quantity = order[3] or 1

            order_code = order[4]
            fullname = order[5] or ""
            phone = order[6] or ""
            product_name = order[7] or ""

            price = order[8] or 0
            deposit = order[9] or 0


            print(
                "CURRENT STATUS:",
                current_status
            )


            # =================================================
            # THANH TOÁN PHẦN CÒN LẠI
            # =================================================

            if is_remaining_payment:

                # =============================================
                # CHỈ XỬ LÝ ĐÚNG TRẠNG THÁI
                #
                # Giúp chống PayOS gửi webhook nhiều lần.
                # =============================================

                if current_status != "Chờ thanh toán phần còn lại":

                    print(
                        "BO QUA REMAINING WEBHOOK - STATUS:",
                        current_status
                    )

                    return "OK", 200


                # =============================================
                # CHỈ ĐƠN CỌC MỚI CÓ THANH TOÁN CÒN LẠI
                # =============================================

                if payment_type != "deposit":

                    print(
                        "BO QUA - KHONG PHAI DON COC"
                    )

                    return "OK", 200


                # =============================================
                # TÍNH SỐ TIỀN CÒN LẠI
                # =============================================

                total_amount = price * quantity
                deposited_amount = deposit * quantity

                expected_amount = max(
                    total_amount - deposited_amount,
                    0
                )


                print(
                    "EXPECTED REMAINING AMOUNT:",
                    expected_amount
                )


                # =============================================
                # KHÔNG CÒN TIỀN PHẢI THANH TOÁN
                # =============================================

                if expected_amount <= 0:

                    print(
                        "KHONG CON TIEN CAN THANH TOAN"
                    )

                    return "OK", 200


                # =============================================
                # SỐ TIỀN KHÔNG ĐỦ
                # =============================================

                if paid_amount < expected_amount:

                    print(
                        "SO TIEN THANH TOAN CON LAI KHONG DU"
                    )

                    return "OK", 200


                # =============================================
                # XÁC NHẬN ĐÃ THANH TOÁN ĐỦ
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
                # Báo Admin khi khách đã thanh toán nốt.
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

                return "OK", 200


            # =================================================
            # THANH TOÁN BAN ĐẦU
            #
            # Logic cọc / full hiện tại.
            # =================================================

            if current_status != "Chưa thanh toán":

                print(
                    "BO QUA WEBHOOK - STATUS:",
                    current_status
                )

                return "OK", 200


            # =================================================
            # XÁC ĐỊNH SỐ TIỀN + TRẠNG THÁI
            # =================================================

            if payment_type == "full":

                expected_amount = (
                    price * quantity
                )

                new_status = (
                    "Đã chuyển khoản full"
                )

            else:

                expected_amount = (
                    deposit * quantity
                )

                new_status = (
                    "Đã cọc"
                )


            print(
                "EXPECTED AMOUNT:",
                expected_amount
            )


            # =================================================
            # SỐ TIỀN KHÔNG ĐỦ
            # =================================================

            if paid_amount < expected_amount:

                print(
                    "SO TIEN THANH TOAN KHONG DU"
                )

                return "OK", 200


            # =================================================
            # XÁC NHẬN THANH TOÁN BAN ĐẦU
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

            updated_rows = cursor.rowcount

            conn.commit()


            # =================================================
            # TELEGRAM
            #
            # Chỉ gửi khi webhook vừa xác nhận thanh toán.
            # =================================================

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
                "PAYMENT SUCCESS:",
                order_code
            )

            print(
                "FINAL STATUS:",
                new_status
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
