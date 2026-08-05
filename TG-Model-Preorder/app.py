from flask import Flask

from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

from routes.home import home_bp
from routes.auth import auth_bp
from routes.preorder import preorder_bp
from routes.admin import admin_bp
from routes.products import products_bp

app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(preorder_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(products_bp)

if __name__ == "__main__":
    app.run(debug=True)