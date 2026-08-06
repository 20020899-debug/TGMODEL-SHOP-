import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db():

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"]
    )

    return conn
