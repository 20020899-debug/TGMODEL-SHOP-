import sqlite3


def get_db():

    conn = sqlite3.connect("orders.db")

    conn.row_factory = sqlite3.Row

    return conn



def init_db():

    conn = get_db()

    cursor = conn.cursor()


    # Bảng sản phẩm

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



if __name__ == "__main__":

    init_db()

    print("Database đã tạo!")