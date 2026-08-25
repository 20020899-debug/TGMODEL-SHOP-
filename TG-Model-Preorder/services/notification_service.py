import os
import urllib.parse
import urllib.request


# =========================================================
# TELEGRAM CONFIG
# =========================================================

TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    ""
)

TELEGRAM_CHAT_ID = os.environ.get(
    "TELEGRAM_CHAT_ID",
    ""
)


# =========================================================
# GỬI TELEGRAM
# =========================================================

def send_telegram_message(message):

    # =====================================================
    # CHƯA CẤU HÌNH
    #
    # Không làm web lỗi nếu thiếu biến môi trường.
    # =====================================================

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram notification chưa được cấu hình")
        return False


    try:

        url = (
            "https://api.telegram.org/bot"
            + TELEGRAM_BOT_TOKEN
            + "/sendMessage"
        )

        data = urllib.parse.urlencode(
            {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            method="POST"
        )

        with urllib.request.urlopen(
            request,
            timeout=10
        ) as response:

            return response.status == 200


    except Exception as error:

        # =================================================
        # TELEGRAM LỖI
        #
        # Không được làm lỗi quá trình đặt hàng hoặc
        # quá trình xác nhận thanh toán.
        # =================================================

        print(
            "LỖI GỬI TELEGRAM:",
            error
        )

        return False


# =========================================================
# THÔNG BÁO ĐƠN HÀNG / THANH TOÁN
#
# payment_type:
#
# full      = khách thanh toán toàn bộ ngay từ đầu
# deposit   = khách thanh toán tiền cọc
# remaining = khách thanh toán phần còn lại của Pre-order
# =========================================================

def send_new_order_notification(
    order_code,
    fullname,
    phone,
    product_name,
    quantity,
    payment_type,
    payment_amount,
    status
):

    # =====================================================
    # NỘI DUNG THEO LOẠI THANH TOÁN
    # =====================================================

    if payment_type == "full":

        title = "🔔 CÓ ĐƠN HÀNG MỚI"
        payment_text = "Chuyển khoản full"

    elif payment_type == "remaining":

        title = "💰 KHÁCH ĐÃ THANH TOÁN PHẦN CÒN LẠI"
        payment_text = "Thanh toán phần còn lại"

    else:

        title = "🔔 CÓ ĐƠN HÀNG MỚI"
        payment_text = "Cọc một phần"


    # =====================================================
    # TẠO NỘI DUNG TELEGRAM
    # =====================================================

    message = (
        f"{title}\n\n"
        f"Mã đơn: {order_code}\n"
        f"Khách: {fullname}\n"
        f"SĐT: {phone}\n\n"
        f"Sản phẩm: {product_name}\n"
        f"Số lượng: {quantity}\n\n"
        f"Thanh toán: {payment_text}\n"
        f"Số tiền: {payment_amount:,} đ\n\n"
        f"Trạng thái: {status}"
    )


    # =====================================================
    # GỬI TELEGRAM
    # =====================================================

    return send_telegram_message(message)
