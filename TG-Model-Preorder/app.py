from flask import Flask, render_template

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
