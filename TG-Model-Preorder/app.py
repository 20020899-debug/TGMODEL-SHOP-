from flask import Flask, render_template, request

app = Flask(__name__)

# Thông tin sản phẩm đang Pre-order
product = {
    "brand": "IN ERA+",
    "name": "IN ERA+ TR-2243EX AZURE FALCON 1/72",
    "price": 1300000,
    "deposit": 300000,
    "eta": "Tháng 9/2026"
}


# Trang chủ
@app.route("/")
def home():
    return render_template("index.html", product=product)


# Trang Pre-order
@app.route("/preorder")
def preorder():
    return render_template("preorder.html", product=product)


# Nhận dữ liệu từ form
@app.route("/submit", methods=["POST"])
def submit():

    fullname = request.form.get("fullname")
    phone = request.form.get("phone")
    contact = request.form.get("contact")
    quantity = request.form.get("quantity")

    province = request.form.get("province")
    district = request.form.get("district")
    ward = request.form.get("ward")
    address_detail = request.form.get("address_detail")

    note = request.form.get("note")

    return f"""
    <h2>Đặt Pre-order thành công!</h2>

    <hr>

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
    """


if __name__ == "__main__":
    app.run(debug=True)
