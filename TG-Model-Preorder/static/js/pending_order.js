let pendingOrderTimer = null;


// =========================================================
// ELEMENT
// =========================================================

const pendingBox =
    document.getElementById(
        "pending-order-box"
    );


const pendingCode =
    document.getElementById(
        "pending-order-code"
    );


const pendingProduct =
    document.getElementById(
        "pending-order-product"
    );


const pendingQuantity =
    document.getElementById(
        "pending-order-quantity"
    );


const pendingStatus =
    document.getElementById(
        "pending-order-status"
    );


const continueButton =
    document.getElementById(
        "continue-payment-button"
    );


const expiredMessage =
    document.getElementById(
        "expired-message"
    );


const preorderButtons =
    document.querySelectorAll(
        ".btn-preorder"
    );


// =========================================================
// KHÓA PRE-ORDER
// =========================================================

function disablePreorderButtons() {

    preorderButtons.forEach(
        function(button) {

            button.classList.add(
                "disabled"
            );


            button.textContent =
                "ĐANG CÓ ĐƠN CHỜ THANH TOÁN";

        }
    );

}


// =========================================================
// MỞ PRE-ORDER
// =========================================================

function enablePreorderButtons() {

    preorderButtons.forEach(
        function(button) {

            button.classList.remove(
                "disabled"
            );


            button.textContent =
                button.dataset.originalText
                || "ĐẶT PRE-ORDER";

        }
    );

}


// =========================================================
// ẨN THÔNG BÁO
// =========================================================

function hidePendingOrder() {

    pendingBox.style.display =
        "none";


    if (pendingOrderTimer) {

        clearInterval(
            pendingOrderTimer
        );

        pendingOrderTimer = null;
    }


    enablePreorderButtons();

}


// =========================================================
// HIỆN ĐƠN
// =========================================================

function showPendingOrder(data) {

    pendingBox.style.display =
        "block";


    pendingCode.textContent =
        data.order_code || "--";


    pendingProduct.textContent =
        data.product_name || "--";


    pendingQuantity.textContent =
        data.quantity || "--";


    pendingStatus.classList.remove(
        "expired"
    );


    expiredMessage.style.display =
        "none";


    // Backend trả UNIX timestamp bằng giây

    const expiresAt =
        Number(data.expires_at) * 1000;


    if (
        !Number.isFinite(expiresAt)
        ||
        expiresAt <= 0
    ) {

        pendingStatus.textContent =
            "Không xác định";


        pendingStatus.classList.add(
            "expired"
        );


        continueButton.style.display =
            "none";


        enablePreorderButtons();


        return;
    }


    // =====================================================
    // TIẾP TỤC THANH TOÁN
    // =====================================================

    continueButton.onclick =
        function() {

            if (data.payment_url) {

                window.location.href =
                    data.payment_url;

            }

        };


    // =====================================================
    // XÓA TIMER CŨ
    // =====================================================

    if (pendingOrderTimer) {

        clearInterval(
            pendingOrderTimer
        );

        pendingOrderTimer = null;
    }


    // =====================================================
    // COUNTDOWN
    // =====================================================

    function updateCountdown() {

        const remaining =
            expiresAt - Date.now();


        // =============================================
        // HẾT HẠN
        // =============================================

        if (remaining <= 0) {

            if (pendingOrderTimer) {

                clearInterval(
                    pendingOrderTimer
                );

                pendingOrderTimer = null;

            }


            pendingStatus.textContent =
                "Hết hạn thanh toán";


            pendingStatus.classList.add(
                "expired"
            );


            continueButton.style.display =
                "none";


            expiredMessage.style.display =
                "block";


            enablePreorderButtons();


            // Backend cập nhật DB thành
            // "Hết hạn thanh toán"

            checkPendingOrder();


            return;
        }


        // =============================================
        // CÒN HẠN
        // =============================================

        pendingStatus.classList.remove(
            "expired"
        );


        expiredMessage.style.display =
            "none";


        continueButton.style.display =
            "inline-block";


        disablePreorderButtons();


        const minutes =
            Math.floor(
                remaining / 60000
            );


        const seconds =
            Math.floor(
                (remaining % 60000)
                / 1000
            );


        pendingStatus.textContent =
            minutes +
            " phút " +
            String(seconds)
                .padStart(2, "0") +
            " giây";

    }


    updateCountdown();


    pendingOrderTimer =
        setInterval(
            updateCountdown,
            1000
        );

}


// =========================================================
// GỌI API PENDING ORDER
// =========================================================

async function checkPendingOrder() {

    try {

        const response =
            await fetch(
                "/api/pending-order",
                {
                    method: "GET",

                    credentials:
                        "same-origin",

                    cache:
                        "no-store"
                }
            );


        if (!response.ok) {

            hidePendingOrder();

            return;
        }


        const data =
            await response.json();


        if (!data.has_order) {

            hidePendingOrder();

            return;
        }


        if (
            data.payment_url
            &&
            data.expires_at
        ) {

            showPendingOrder(
                data
            );

        }

        else {

            hidePendingOrder();

        }

    }

    catch (error) {

        console.error(
            "Lỗi kiểm tra đơn:",
            error
        );

    }

}


// =========================================================
// LOAD
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        checkPendingOrder();

    }
);


// =========================================================
// KIỂM TRA 30 GIÂY / LẦN
// =========================================================

setInterval(
    checkPendingOrder,
    30000
);