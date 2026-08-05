from flask import Flask

from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

from routes.home import home_bp
from routes.auth import auth_bp
from routes.preorder import preorder_bp
from routes.admin import admin_bp

app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(preorder_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True)
import sqlite3


def init_database():

    conn = sqlite3.connect("orders.db")

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        brand TEXT,

        name TEXT,

        price INTEGER,

        deposit INTEGER,

        eta TEXT,

        image TEXT,

        status TEXT

    )
    """)


    conn.commit()
    conn.close()



init_database()