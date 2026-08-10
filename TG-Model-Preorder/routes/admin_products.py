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


    # =====================================================
    # DỮ LIỆU TEXT
    # =====================================================

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


    image_url = request.form.get(
        "image_url",
        ""
    ).strip()


    # =====================================================
    # DỮ LIỆU SỐ
    # =====================================================

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


    # =====================================================
    # KIỂM TRA TÊN
    # =====================================================

    if not name:

        return (
            "Tên sản phẩm không được để trống",
            400
        )


    # =====================================================
    # KHÔNG CHO GIÁ TRỊ ÂM
    # =====================================================

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


    # =====================================================
    # DATABASE
    # =====================================================

    conn = get_db()

    cursor = conn.cursor()


    try:

        # =================================================
        # THÊM PRODUCT
        # =================================================

        cursor.execute(
            """
            INSERT INTO products
            (
                name,
                brand,
                price,
                deposit,
                eta,
                image_url,
                active
            )

            VALUES
            (
                %s,
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
                eta,
                image_url
            )
        )


        product_id = (
            cursor.fetchone()[0]
        )


        # =================================================
        # TẠO TỒN KHO
        # =================================================

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

        # =================================================
        # POST - LƯU SỬA
        # =================================================

        if request.method == "POST":

            # =============================================
            # TEXT
            # =============================================

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


            image_url = request.form.get(
                "image_url",
                ""
            ).strip()


            # =============================================
            # ACTIVE
            # =============================================

            active = (
                request.form.get(
                    "active"
                )
                == "1"
            )


            # =============================================
            # NUMBER
            # =============================================

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


            # =============================================
            # KIỂM TRA TÊN
            # =============================================

            if not name:

                return (
                    "Tên sản phẩm không được để trống",
                    400
                )


            # =============================================
            # KHÔNG CHO GIÁ TRỊ ÂM
            # =============================================

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


            # =============================================
            # UPDATE PRODUCT
            # =============================================

            cursor.execute(
                """
                UPDATE products

                SET
                    name=%s,
                    brand=%s,
                    price=%s,
                    deposit=%s,
                    eta=%s,
                    image_url=%s,
                    active=%s

                WHERE id=%s
                """,
                (
                    name,
                    brand,
                    price,
                    deposit,
                    eta,
                    image_url,
                    active,
                    product_id
                )
            )


            # =============================================
            # UPDATE STOCK
            # =============================================

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


        # =================================================
        # GET - LẤY PRODUCT
        # =================================================

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


# =========================================================
# XÓA SẢN PHẨM
# =========================================================

@admin_products_bp.route(
    "/admin/products/<int:product_id>/delete",
    methods=["POST"]
)
def delete_product(
    product_id
):

    if not session.get("admin"):

        return redirect(
            url_for(
                "auth.login"
            )
        )


    conn = get_db()

    cursor = conn.cursor()


    try:

        # =================================================
        # KIỂM TRA PRODUCT
        # =================================================

        cursor.execute(
            """
            SELECT id

            FROM products

            WHERE id=%s

            LIMIT 1
            """,
            (
                product_id,
            )
        )


        product = cursor.fetchone()


        if product is None:

            return (
                "Không tìm thấy sản phẩm",
                404
            )


        # =================================================
        # KIỂM TRA ĐÃ TỪNG CÓ ĐƠN CHƯA
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*)

            FROM orders

            WHERE product_id=%s
            """,
            (
                product_id,
            )
        )


        order_count = (
            cursor.fetchone()[0]
        )


        # =================================================
        # ĐÃ TỪNG CÓ ĐƠN
        #
        # Không xóa cứng để giữ lịch sử.
        # Chỉ ẩn sản phẩm.
        # =================================================

        if order_count > 0:

            cursor.execute(
                """
                UPDATE products

                SET active=FALSE

                WHERE id=%s
                """,
                (
                    product_id,
                )
            )


            conn.commit()


            return redirect(
                url_for(
                    "admin_products.products"
                )
            )


        # =================================================
        # CHƯA TỪNG CÓ ĐƠN
        # XÓA STOCK
        # =================================================

        cursor.execute(
            """
            DELETE FROM product_stock

            WHERE product_id=%s
            """,
            (
                product_id,
            )
        )


        # =================================================
        # XÓA PRODUCT
        # =================================================

        cursor.execute(
            """
            DELETE FROM products

            WHERE id=%s
            """,
            (
                product_id,
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
