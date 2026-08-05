from flask import Blueprint, render_template, request, redirect, url_for, session
import sqlite3


products_bp = Blueprint(
    "products",
    __name__
)


# ==========================
# DANH SÁCH SẢN PHẨM
# ==========================

@products_bp.route("/admin/products")
def products():

    if not session.get("admin"):
        return redirect(
            url_for("auth.login")
        )


    conn = sqlite3.connect(
        "orders.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)


    products = cursor.fetchall()


    conn.close()


    return render_template(
        "products.html",
        products=products
    )



# ==========================
# THÊM SẢN PHẨM
# ==========================

@products_bp.route(
    "/admin/products/add",
    methods=["GET", "POST"]
)
def add_product():

    if not session.get("admin"):
        return redirect(
            url_for("auth.login")
        )


    if request.method == "POST":


        brand = request.form.get("brand")

        name = request.form.get("name")

        price = int(
            request.form.get("price")
        )

        deposit = int(
            request.form.get("deposit")
        )

        eta = request.form.get("eta")

        image = request.form.get("image")

        status = request.form.get("status")



        conn = sqlite3.connect(
            "orders.db"
        )

        cursor = conn.cursor()



        cursor.execute("""
            INSERT INTO products
            (
                brand,
                name,
                price,
                deposit,
                eta,
                image,
                status
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)

        """,
        (
            brand,
            name,
            price,
            deposit,
            eta,
            image,
            status
        ))



        conn.commit()

        conn.close()



        return redirect(
            url_for("products.products")
        )



    return render_template(
        "add_product.html"
    )



# ==========================
# XÓA SẢN PHẨM
# ==========================

@products_bp.route(
    "/admin/products/<int:id>/delete",
    methods=["POST"]
)
def delete_product(id):

    if not session.get("admin"):
        return redirect(
            url_for("auth.login")
        )


    conn = sqlite3.connect(
        "orders.db"
    )

    cursor = conn.cursor()



    cursor.execute(
        """
        DELETE FROM products
        WHERE id=?
        """,
        (id,)
    )



    conn.commit()

    conn.close()



    return redirect(
        url_for("products.products")
    )