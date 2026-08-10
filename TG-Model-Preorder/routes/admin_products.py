from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from psycopg2.extras import RealDictCursor

from database import get_db

from services.product_service import (
    get_all_products,
    get_product
)


admin_products_bp = Blueprint(
    "admin_products",
    __name__
)


# =========================================================
# DANH SÁCH SẢN PHẨM
# =========================================================

@admin_products_bp.route(
    "/admin/products"
)
def products():

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        product_list = get_all_products(
            cursor
        )


        return render_template(
            "admin_products.html",
            products=product_list
        )


    finally:

        cursor.close()
        conn.close()


# =========================================================
# THÊM SẢN PHẨM
# =========================================================

@admin_products_bp.route(
    "/admin/products/add",
    methods=["POST"]
)
def add_product():

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    name = request.form.get(
        "name",
        ""
    ).strip()


    brand = request.form.get(
        "brand",
        ""
    ).strip()


    eta = request.form.get(
        "eta",
        ""
    ).strip()


    try:

        price = int(
            request.form.get(
                "price",
                0
            )
        )

        deposit = int(
            request.form.get(
                "deposit",
                0
            )
        )

        stock = int(
            request.form.get(
                "stock",
                0
            )
        )

    except (TypeError, ValueError):

        return (
            "Dữ liệu sản phẩm không hợp lệ",
            400
        )


    if not name:

        return (
            "Tên sản phẩm không được để trống",
            400
        )


    if price < 0:
        price = 0

    if deposit < 0:
        deposit = 0

    if stock < 0:
        stock = 0


    conn = get_db()
    cursor = conn.cursor()


    try:

        cursor.execute(
            """
            INSERT INTO products
            (
                name,
                brand,
                price,
                deposit,
                eta,
                active
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                TRUE
            )

            RETURNING id
            """,
            (
                name,
                brand,
                price,
                deposit,
                eta
            )
        )


        product_id = (
            cursor.fetchone()[0]
        )


        cursor.execute(
            """
            INSERT INTO product_stock
            (
                product_id,
                stock
            )

            VALUES
            (
                %s,
                %s
            )
            """,
            (
                product_id,
                stock
            )
        )


        conn.commit()


    except Exception:

        conn.rollback()

        raise


    finally:

        cursor.close()
        conn.close()


    return redirect(
        url_for(
            "admin_products.products"
        )
    )


# =========================================================
# SỬA SẢN PHẨM
# =========================================================

@admin_products_bp.route(
    "/admin/products/<int:product_id>/edit",
    methods=["GET", "POST"]
)
def edit_product(
    product_id
):

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    try:

        if request.method == "POST":

            name = request.form.get(
                "name",
                ""
            ).strip()


            brand = request.form.get(
                "brand",
                ""
            ).strip()


            eta = request.form.get(
                "eta",
                ""
            ).strip()


            active = (
                request.form.get(
                    "active"
                )
                == "1"
            )


            try:

                price = int(
                    request.form.get(
                        "price",
                        0
                    )
                )

                deposit = int(
                    request.form.get(
                        "deposit",
                        0
                    )
                )

                stock = int(
                    request.form.get(
                        "stock",
                        0
                    )
                )

            except (TypeError, ValueError):

                return (
                    "Dữ liệu không hợp lệ",
                    400
                )


            if not name:

                return (
                    "Tên sản phẩm không được để trống",
                    400
                )


            price = max(
                price,
                0
            )

            deposit = max(
                deposit,
                0
            )

            stock = max(
                stock,
                0
            )


            cursor.execute(
                """
                UPDATE products

                SET
                    name=%s,
                    brand=%s,
                    price=%s,
                    deposit=%s,
                    eta=%s,
                    active=%s

                WHERE id=%s
                """,
                (
                    name,
                    brand,
                    price,
                    deposit,
                    eta,
                    active,
                    product_id
                )
            )


            cursor.execute(
                """
                INSERT INTO product_stock
                (
                    product_id,
                    stock
                )

                VALUES
                (
                    %s,
                    %s
                )

                ON CONFLICT (product_id)

                DO UPDATE SET
                    stock=EXCLUDED.stock
                """,
                (
                    product_id,
                    stock
                )
            )


            conn.commit()


            return redirect(
                url_for(
                    "admin_products.products"
                )
            )


        product = get_product(
            cursor,
            product_id
        )


        if product is None:

            return (
                "Không tìm thấy sản phẩm",
                404
            )


        return render_template(
            "admin_product_edit.html",
            product=product
        )


    except Exception:

        conn.rollback()

        raise


    finally:

        cursor.close()
        conn.close()