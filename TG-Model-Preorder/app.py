from flask import Flask, render_template, request
app = Flask(__name__)

product = {
    "brand": "IN ERA+",
    "name": "IN ERA+ TR-2243EX AZURE FALCON 1/72",
    "price": 1300000,
    "deposit": 300000,
    "eta": "Tháng 9/2026"
}

@app.route("/")
def home():
    return render_template("index.html", product=product)

@app.route("/preorder")
def preorder():
    return render_template("preorder.html", product=product)

if __name__ == "__main__":
    app.run(debug=True)
@app.route("/submit", methods=["POST"])
def submit():

    fullname = request.form["fullname"]
    phone = request.form["phone"]
    facebook = request.form["facebook"]
    province = request.form["province"]
    district = request.form["district"]
    ward = request.form["ward"]
    address_detail = request.form["address_detail"]
    quantity = request.form["quantity"]
    note = request.form["note"]

    return f"""
    <h2>Đã nhận đơn</h2>

    Tên: {fullname}<br>
    SĐT: {phone}<br>
    Facebook/Zalo: {facebook}<br>
    Địa chỉ: {address_detail}, {ward}, {district}, {province}<br>
    Số lượng: {quantity}<br>
    Ghi chú: {note}
    """
