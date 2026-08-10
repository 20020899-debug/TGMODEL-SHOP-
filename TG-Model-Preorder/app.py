from flask import Flask

from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

from routes.home import home_bp
from routes.auth import auth_bp
from routes.preorder import preorder_bp
from routes.admin import admin_bp
from routes.payment import payment_bp
from routes.pending_order import pending_order_bp
from routes.preorder_page import preorder_page_bp

app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(preorder_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(pending_order_bp)
app.register_blueprint(preorder_page_bp)

if __name__ == "__main__":
    app.run(debug=True)
