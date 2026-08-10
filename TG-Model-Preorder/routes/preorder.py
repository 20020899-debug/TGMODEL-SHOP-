from flask import (
    Blueprint,
    request,
    redirect,
    make_response,
    render_template
)

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import time
import secrets

from database import get_db
from config import products
from payos_service import payos


# =========================================================
# MÚI GIỜ VIỆT NAM
# =========================================================

VIETNAM_TZ = ZoneInfo(
    "Asia/Ho_Chi_Minh"
)


preorder_bp = Blueprint(
    "preorder",
    __name__
)


# =========================================================
# CHUẨN HÓA THỜI GIAN DATABASE
# =========================================================

def normalize_expires_at(expires_at):

    if expires_at is None:
        return None

    # Database đang lưu TIMESTAMP không timezone.
    # Quy ước giá trị trong DB là giờ Việt Nam.

    if expires_at.tzinfo is None:

        expires_at = expires_at.replace(
            tzinfo=VIETNAM_TZ
        )

    else:

        expires_at = expires_at.astimezone(
            VIETNAM_TZ
        )

    return expires_at


