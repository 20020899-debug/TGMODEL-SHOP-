from flask import (
    Blueprint,
    request
)

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
# =========================================================

@payment_webhook_bp.route(
    "/payment/webhook",
    methods=["POST"]
)
def webhook():

    print(
        "========== PAYOS WEBHOOK =========="
    )


    try:

        # =================================================
        # XÁC MINH WEBHOOK BẰNG PAYOS SDK
        # =================================================

        webhook_data = (
            payos.webhooks.verify(
                request.data
            )
        )


        print(
            "WEBHOOK VERIFIED:",
            webhook_data
        )


        # =================================================
        # LẤY THÔNG TIN PAYOS
        # =================================================

        order_code = (
            webhook_data.description
        )


        paid_amount = (
            webhook_data.amount
        )


        print(
            "ORDER CODE:",
            order_code
        )

        print(
            "PAID AMOUNT:",
            paid_amount
        )


        if not order_code:

            return (
                "OK",
                200
            )


        # =================================================
        # DATABASE
        # =================================================

        conn = get_db()

        cursor = conn.cursor()


        try:

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
                (
                    order_code,
                )
            )


            order = cursor.fetchone()


            # =============================================
            # KHÔNG TÌM THẤY ĐƠN
            # =============================================

            if order is None:

                print(
                    "KHONG TIM THAY DON:",
                    order_code
                )

                return (
                    "OK",
                    200
                )


            order_id = (
                order[0]
            )

            current_status = (
                order[1]
            )

            payment_type = (
                order[2]
            )

            quantity = (
                order[3]
                or 1
            )

            order_code = (
                order[4]
            )

            fullname = (
                order[5]
                or ""
            )

            phone = (
                order[6]
                or ""
            )

            product_name = (
                order[7]
                or ""
            )

            price = (
                order[8]
                or 0
            )

            deposit = (
                order[9]
                or 0
            )


            print(
                "CURRENT STATUS:",
                current_status
            )


            # =============================================
            # CHỈ XỬ LÝ ĐƠN ĐANG CHỜ THANH TOÁN
            #
            # Giúp chống webhook gọi lại nhiều lần.
            # =============================================

            if current_status != "Chưa thanh toán":

                print(
                    "BO QUA WEBHOOK - STATUS:",
                    current_status
                )

                return (
                    "OK",
                    200
                )


            # =============================================
            # KIỂM TRA SỐ TIỀN
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
                "EXPECTED AMOUNT:",
                expected_amount
            )


            # =============================================
            # SỐ TIỀN KHÔNG KHỚP
            # =============================================

            if paid_amount < expected_amount:

                print(
                    "SO TIEN THANH TOAN KHONG DU"
                )

                return (
                    "OK",
                    200
                )


            # =============================================
            # UPDATE ĐƠN
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


            updated_rows = (
                cursor.rowcount
            )


            conn.commit()


            print(
                "UPDATED ROWS:",
                updated_rows
            )


            # =============================================
            # TELEGRAM
            #
            # CHỈ BÁO KHI ĐƠN VỪA ĐƯỢC
            # XÁC NHẬN THANH TOÁN.
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
                "PAYMENT SUCCESS:",
                order_code
            )

            print(
                "FINAL STATUS:",
                new_status
            )


            return (
                "OK",
                200
            )


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


        return (
            "INVALID WEBHOOK",
            400
        )
