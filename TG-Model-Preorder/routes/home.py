from flask import Blueprint, render_template
import sqlite3

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def home():

    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM products
        WHERE status='active'
        ORDER BY id DESC
    """)


    products = cursor.fetchall()


    conn.close()


    return render_template(
        "index.html",
        products=products
    )