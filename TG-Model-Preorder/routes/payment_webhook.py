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
# Xử lý 2 loại thanh toán:
# 1. Thanh toán ban đầu
#    Description:
#    TGM001
#    → Đã cọc
#    hoặc
#    → Đã chuyển khoản full
#
#
# 2. Thanh toán phần còn lại của Pre-order
#
#    Description:
#    TGM001REM
#
#    → Đã thanh toán đủ
#
# LƯU Ý:
# PayOS có thể loại bỏ ký tự "-" trong description,
# vì vậy phần thanh toán còn lại sử dụng:
#
# TGM001REM
#
# thay vì:
#
# TGM001-REM
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
        # XÁC MINH WEBHOOK PAYOS
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
        # LẤY THÔNG TIN THANH TOÁN
        # =================================================

        description = (
            webhook_data.description
            or ""
        ).strip()


        paid_amount = (
            webhook_data.amount
            or 0
        )


        print(
            "DESCRIPTION:",
            description
        )

        print(
            "PAID AMOUNT:",
            paid_amount
        )


        # =================================================
        # KHÔNG CÓ DESCRIPTION
        # =================================================

        if not description:

            print(
                "WEBHOOK KHONG CO DESCRIPTION"
            )

            return (
                "OK",
                200
            )


        # =================================================
        # XÁC ĐỊNH LOẠI THANH TOÁN
        #
        # Thanh toán ban đầu:
        #
        # TGM136
        #
        # Thanh toán phần còn lại:
        #
        # TGM136REM
        #
        # REM có 3 ký tự.
        #
        # Vì vậy:
        #
        # TGM136REM
        #       ↓
        # description[:-3]
        #       ↓
        # TGM136
        # =================================================

        is_remaining_payment = (
            description.endswith(
                "REM"
            )
        )


        if is_remaining_payment:

            order_code = (
                description[:-3]
            )

        else:

            order_code = (
                description
            )


        print(
            "ORDER CODE:",
            order_code
        )

        print(
            "REMAINING PAYMENT:",
            is_remaining_payment
        )


        # =================================================
        # DATABASE
        # =================================================

        conn = get_db()

        cursor = conn.cursor()


        try:

            # =================================================
            # KHÓA ĐƠN
            #
            # FOR UPDATE giúp tránh trường hợp hai webhook
            # xử lý cùng một đơn tại cùng thời điểm.
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
                (
                    order_code,
                )
            )


            order = (
                cursor.fetchone()
            )


            # =================================================
            # KHÔNG TÌM THẤY ĐƠN
            # =================================================

            if order is None:

                print(
                    "KHONG TIM THAY DON:",
                    order_code
                )

                return (
                    "OK",
                    200
                )


            # =================================================
            # LẤY DỮ LIỆU ĐƠN
            # =================================================

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


            # =================================================
            # =================================================
            #
            # THANH TOÁN PHẦN CÒN LẠI
            #
            # =================================================
            # =================================================

            if is_remaining_payment:


                print(
                    "XU LY THANH TOAN PHAN CON LAI"
                )


                # =============================================
                # CHỈ ĐƠN CỌC MỚI ĐƯỢC THANH TOÁN CÒN LẠI
                # =============================================

                if payment_type != "deposit":

                    print(
                        "BO QUA REMAINING - "
                        "KHONG PHAI DON COC"
                    )

                    return (
                        "OK",
                        200
                    )


                # =============================================
                # KIỂM TRA TRẠNG THÁI
                #
                # Chỉ xử lý khi Admin đã chuyển đơn sang:
                #
                # Chờ thanh toán phần còn lại
                #
                # Đồng thời chống webhook gọi lại nhiều lần.
                # =============================================

                if (
                    current_status
                    !=
                    "Chờ thanh toán phần còn lại"
                ):

                    print(
                        "BO QUA REMAINING WEBHOOK - STATUS:",
                        current_status
                    )

                    return (
                        "OK",
                        200
                    )


                # =============================================
                # TÍNH SỐ TIỀN CÒN LẠI
                #
                # Tổng tiền:
                #
                # price × quantity
                #
                # Đã cọc:
                #
                # deposit × quantity
                #
                # Còn lại:
                #
                # (price - deposit) × quantity
                # =============================================

                expected_amount = max(
                    (
                        price
                        -
                        deposit
                    )
                    *
                    quantity,
                    0
                )


                print(
                    "EXPECTED REMAINING AMOUNT:",
                    expected_amount
                )


                # =============================================
                # KIỂM TRA SỐ TIỀN
                # =============================================

                if (
                    paid_amount
                    <
                    expected_amount
                ):

                    print(
                        "SO TIEN THANH TOAN "
                        "CON LAI KHONG DU"
                    )

                    print(
                        "PAID:",
                        paid_amount
                    )

                    print(
                        "EXPECTED:",
                        expected_amount
                    )

                    return (
                        "OK",
                        200
                    )


                # =============================================
                # CẬP NHẬT ĐƠN
                #
                # Chờ thanh toán phần còn lại
                #
                #              ↓
                #
                # Đã thanh toán đủ
                #
                #
                # Đồng thời xóa link PayOS phần còn lại.
                #
                # KHÔNG thay đổi tồn kho.
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


                updated_rows = (
                    cursor.rowcount
                )


                conn.commit()


                print(
                    "REMAINING UPDATED ROWS:",
                    updated_rows
                )


                # =============================================
                # TELEGRAM
                #
                # Chỉ gửi khi database thực sự vừa được
                # cập nhật.
                #
                # Nếu PayOS gọi webhook lần thứ hai:
                #
                # status đã là "Đã thanh toán đủ"
                #
                # → webhook phía trên sẽ bỏ qua.
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
                        "TELEGRAM REMAINING RESULT:",
                        telegram_result
                    )


                # =============================================
                # HOÀN TẤT
                # =============================================

                print(
                    "REMAINING PAYMENT SUCCESS:",
                    order_code
                )

                print(
                    "FINAL STATUS:",
                    "Đã thanh toán đủ"
                )


                return (
                    "OK",
                    200
                )


            # =================================================
            # =================================================
            #
            # THANH TOÁN BAN ĐẦU
            #
            # =================================================
            # =================================================


            print(
                "XU LY THANH TOAN BAN DAU"
            )


            # =================================================
            # CHỈ XỬ LÝ ĐƠN CHƯA THANH TOÁN
            #
            # Đồng thời chống webhook PayOS gọi lại.
            # =================================================

            if (
                current_status
                !=
                "Chưa thanh toán"
            ):

                print(
                    "BO QUA INITIAL WEBHOOK - STATUS:",
                    current_status
                )

                return (
                    "OK",
                    200
                )


            # =================================================
            # TÍNH SỐ TIỀN THANH TOÁN BAN ĐẦU
            # =================================================

            if payment_type == "full":

                expected_amount = (
                    price
                    *
                    quantity
                )


                new_status = (
                    "Đã chuyển khoản full"
                )


            elif payment_type == "deposit":

                expected_amount = (
                    deposit
                    *
                    quantity
                )


                new_status = (
                    "Đã cọc"
                )


            else:

                print(
                    "PAYMENT TYPE KHONG HOP LE:",
                    payment_type
                )

                return (
                    "OK",
                    200
                )


            print(
                "EXPECTED INITIAL AMOUNT:",
                expected_amount
            )


            # =================================================
            # KIỂM TRA SỐ TIỀN
            # =================================================

            if (
                paid_amount
                <
                expected_amount
            ):

                print(
                    "SO TIEN THANH TOAN KHONG DU"
                )

                print(
                    "PAID:",
                    paid_amount
                )

                print(
                    "EXPECTED:",
                    expected_amount
                )

                return (
                    "OK",
                    200
                )


            # =================================================
            # UPDATE THANH TOÁN BAN ĐẦU
            #
            # Nếu cọc:
            #
            # Chưa thanh toán
            #       ↓
            # Đã cọc
            #
            #
            # Nếu thanh toán full:
            #
            # Chưa thanh toán
            #       ↓
            # Đã chuyển khoản full
            #
            #
            # Hàng đã bị trừ khi tạo đơn nên:
            #
            # stock_reserved = FALSE
            #
            # KHÔNG trừ kho thêm.
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
                "INITIAL UPDATED ROWS:",
                updated_rows
            )


            # =================================================
            # TELEGRAM
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


            # =================================================
            # HOÀN TẤT
            # =================================================

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


    # =====================================================
    # WEBHOOK KHÔNG HỢP LỆ / LỖI KHÁC
    # =====================================================

    except Exception as error:

        print(
            "INVALID PAYOS WEBHOOK:",
            error
        )


        return (
            "INVALID WEBHOOK",
            400
        )
