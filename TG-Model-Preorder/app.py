from flask import Flask, render_template

app = Flask(__name__)

product = {
    "name": "MS GENERAL FALCON",
    "price": 2390000,
    "deposit": 500000,
    "arrival": "Tháng 11/2026",
    "description": "Phiên bản Pre-order chính hãng."
}

@app.route("/")
def home():
    return render_template("index.html", product=product)

if __name__ == "__main__":
    app.run(debug=True)
