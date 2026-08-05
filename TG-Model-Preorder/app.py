from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "TGMODELSHOP2026"


# ==========================
# TÀI KHOẢN ADMIN
# ==========================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123456"


# ==========================
# THÔNG TIN SẢN PHẨM
# ==========================

product = {
    "brand": "IN ERA+",
    "name": "IN ERA+ TR-2243EX AZURE FALCON 1/72",
    "price": 1300000,
    "deposit": 300000,
    "eta": "Tháng 9/2026"
}


# ==========================
# TRANG CHỦ
# ==========================

@app.route("/")
def home():
    return render_template("index.html", product=product)


# ==========================
# PREORDER
# ==========================

@app.route("/preorder")
def preorder():
    return render_template("preorder.html", product=product)


# ==========================
# ĐĂNG NHẬP ADMIN
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session["admin"] = True

            return redirect(url_for("admin"))

        return render_template(
            "login.html",
            error="Sai tài khoản hoặc mật khẩu!"
        )

    return render_template("login.html")


# ==========================
# ĐĂNG XUẤT
# ==========================

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect(url_for("login"))


# ==========================
# NHẬN ĐƠN PREORDER
# ==========================

@app.route("/submit", methods=["POST"])
def submit():

    fullname = request.form.get("fullname")
    phone = request.form.get("phone")
    contact = request.form.get("contact")

    province = request.form.get("province")
    district = request.form.get("district")
    ward = request.form.get("ward")
    address_detail = request.form.get("address_detail")

    quantity = int(request.form.get("quantity", 1))

    note = request.form.get("note")

    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0] + 1

    order_code = f"TG{count:06d}"
    created_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cursor.execute("""
        INSERT INTO orders (
            order_code,
            fullname,
            phone,
            contact,
            province,
            district,
            ward,
            address_detail,
            quantity,
            note,
            product_name,
            product_brand,
            price,
            deposit,
            status
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
    order_code,
    fullname,
    phone,
    contact,
    province,
    district,
    ward,
    address_detail,
    quantity,
    note,
    product["name"],
    product["brand"],
    product["price"],
    product["deposit"],
    "Chưa thanh toán",
    created_at
))

    conn.commit()
    conn.close()

    return f"""
    <h2>Đặt Pre-order thành công!</h2>

    <hr>

    <b>Mã đơn:</b> {order_code}<br><br>

    <b>Họ tên:</b> {fullname}<br>
    <b>Số điện thoại:</b> {phone}<br>
    <b>Facebook/Zalo:</b> {contact}<br>
    <b>Địa chỉ:</b> {address_detail}, {ward}, {district}, {province}<br>
    <b>Số lượng:</b> {quantity}<br>
    <b>Ghi chú:</b> {note}<br>

    <hr>

    <h3>Sản phẩm</h3>

    <b>Hãng:</b> {product["brand"]}<br>
    <b>Tên:</b> {product["name"]}<br>
    <b>Giá:</b> {product["price"]:,} đ<br>
    <b>Tiền cọc:</b> {product["deposit"]:,} đ<br>
    <b>Dự kiến:</b> {product["eta"]}<br>

    <hr>

    <h3>Trạng thái: Chưa thanh toán</h3>

    <br><br>

    <a href="/">Quay về trang chủ</a>
    """


# ==========================
# TRANG QUẢN LÝ ĐƠN HÀNG
# ==========================

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        orders=orders
    )


# ==========================
# CHẠY FLASK
# ==========================

if __name__ == "__main__":
    app.run(debug=True)
