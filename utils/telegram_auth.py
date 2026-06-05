import hashlib
import hmac
import json
import os
from urllib.parse import unquote, parse_qs

from fastapi import Header, HTTPException, status


def _validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    parsed = parse_qs(init_data)
    items = {k: unquote(v[0]) for k, v in parsed.items()}

    hash_check = items.pop("hash", None)
    if not hash_check:
        return None

    sorted_items = sorted(items.items(), key=lambda x: x[0])
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if computed_hash != hash_check:
        return None

    if "user" in items:
        items["user"] = json.loads(items["user"])

    return items


async def get_miniapp_user(
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
    x_telegram_user_id: str | None = Header(None, alias="X-Telegram-User-Id"),
):
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        raise HTTPException(status_code=500, detail="TELEGRAM_TOKEN not configured")

    user_data = None

    if x_telegram_init_data:
        validated = _validate_telegram_init_data(x_telegram_init_data, bot_token)
        if validated and validated.get("user"):
            user_data = validated["user"]

    # fallback for local dev / direct header
    if not user_data and x_telegram_user_id:
        user_data = {"id": x_telegram_user_id, "first_name": "User"}

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Telegram authentication",
        )

    telegram_id = str(user_data["id"])
    name = user_data.get("first_name", "User")

    from db.controller.userController import (
        get_user_by_telegram,
        create_user_from_telegram,
        get_user_info,
    )

    existing = get_user_by_telegram(telegram_id)
    if existing:
        user_id = str(existing["id"])
    else:
        user_id = create_user_from_telegram(telegram_id, name)

    user = get_user_info(user_id)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to resolve user")

    return user_id, user
