import os

from flask import Flask

from routes.home import home_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.pending_order import pending_order_bp
from routes.preorder_page import preorder_page_bp
from routes.submit_order import submit_order_bp
from routes.payment_success import payment_success_bp
from routes.payment_cancel import payment_cancel_bp
from routes.payment_webhook import payment_webhook_bp
from routes.admin_stock import admin_stock_bp
from routes.admin_products import admin_products_bp


# =========================================================
# KHỞI TẠO FLASK
# =========================================================

app = Flask(
    __name__
)


# =========================================================
# SECRET KEY
#
# Render:
# Environment
# → SECRET_KEY
# =========================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "tgmodel-dev-secret-key"
)


# =========================================================
# REGISTER BLUEPRINTS
# =========================================================

app.register_blueprint(
    home_bp
)


app.register_blueprint(
    auth_bp
)


app.register_blueprint(
    admin_bp
)


app.register_blueprint(
    pending_order_bp
)


app.register_blueprint(
    preorder_page_bp
)


app.register_blueprint(
    submit_order_bp
)


app.register_blueprint(
    payment_success_bp
)


app.register_blueprint(
    payment_cancel_bp
)


app.register_blueprint(
    payment_webhook_bp
)


app.register_blueprint(
    admin_stock_bp
)


app.register_blueprint(
    admin_products_bp
)


# =========================================================
# CHẠY LOCAL
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
