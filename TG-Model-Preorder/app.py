from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# ==========================
# Thông tin sản phẩm
# ==========================
product = {
    "brand": "IN ERA+",
    "name": "IN ERA+ TR-2243EX AZURE FALCON 1/72",
    "price": 1300000,
    "deposit": 300000,
    "eta": "Tháng 9/2026"
}


# ==========================
# Trang chủ
# ==========================
@app.route("/")
def home():
    return render_template("index.html", product=product)


# ==========================
# Trang Pre-order
# ==========================
@app.route("/preorder")
def preorder():
    return render_template("preorder.html", product=product)


# ==========================
# Nhận đơn hàng
# ==========================
@app.route("/submit", methods=["POST"])
def submit():

    fullname = request.form.get("fullname")
    phone = request.form.get("phone")
    contact = request.form.get("contact")

    quantity = int(request.form.get("quantity"))

    province = request.form.get("province")
    district = request.form.get("district")
    ward = request.form.get("ward")
    address_detail = request.form.get("address_detail")

    note = request.form.get("note")

    # Kết nối database
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()

    # Sinh mã đơn
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0] + 1
    order_code = f"TG{count:06d}"

    # Lưu đơn
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        "Chưa thanh toán"
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

    <h3>Sản phẩm đã đặt</h3>

    <b>Hãng:</b> {product["brand"]}<br>
    <b>Tên:</b> {product["name"]}<br>
    <b>Giá:</b> {product["price"]:,} đ<br>
    <b>Tiền cọc:</b> {product["deposit"]:,} đ<br>
    <b>Dự kiến trả hàng:</b> {product["eta"]}<br>

    <hr>

    <h3>Trạng thái: Chưa thanh toán</h3>
    """


# ==========================
# Trang quản lý đơn hàng
# ==========================
@app.route("/admin")
def admin():

    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders ORDER BY id DESC")

    orders = cursor.fetchall()

    conn.close()

    return render_template("admin.html", orders=orders)


# ==========================
# Chạy Flask
# ==========================
if __name__ == "__main__":
    app.run(debug=True)
