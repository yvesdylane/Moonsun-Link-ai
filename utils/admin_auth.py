import os
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.controller.userController import get_user_by_phone, generate_linking_code, verify_linking_code, get_user_info

security = HTTPBearer()

JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "fallback-dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    user = get_user_info(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user_id, user


def send_admin_code(phone: str, code: str, user_row: dict):
    whatsapp_chat_id = user_row.get("whatsapp_chat_id")
    telegram_id = user_row.get("telegram_id")
    message = f"🔐 Your Moonso Link admin verification code is: {code}\n\nCode expires in 5 minutes."

    if whatsapp_chat_id:
        try:
            from utils.whatsapp import send_whatsapp_reply
            send_whatsapp_reply(whatsapp_chat_id, message)
        except Exception as e:
            print(f"ADMIN LOGIN WHATSAPP SEND ERROR: {e}")

    if telegram_id:
        try:
            import requests
            tg_token = os.getenv("TELEGRAM_TOKEN")
            if tg_token:
                tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
                requests.post(tg_url, json={
                    "chat_id": telegram_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }, timeout=10)
        except Exception as e:
            print(f"ADMIN LOGIN TELEGRAM SEND ERROR: {e}")

    if not whatsapp_chat_id and not telegram_id:
        print(f"WARNING: Admin {phone} has no WhatsApp chat_id or Telegram ID to send code")
