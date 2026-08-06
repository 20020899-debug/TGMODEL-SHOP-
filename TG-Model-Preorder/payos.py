import os
import requests

CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
API_KEY = os.getenv("PAYOS_API_KEY")
CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")


def test():

    return {
        "client": CLIENT_ID,
        "api": API_KEY,
        "checksum": CHECKSUM_KEY
    }