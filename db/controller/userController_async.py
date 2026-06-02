"""
Async version of userController.

This is the async rewrite of userController.py
Once fully migrated, this will replace the sync version.
"""

from db.connect import get_async_connection
from db.models.user import User
from psycopg.rows import dict_row


async def get_user_info(user_id: str) -> User:
    """Get user information by ID."""
    async with get_async_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("""
                SELECT id, name, phone, email, role, region, verified, pic_folder
                FROM users
                WHERE id = %s
            """, (user_id,))
            result = await cur.fetchone()

    if not result:
        return None

    return User(
        id=str(result['id']),
        name=result['name'],
        phone=result['phone'],
        email=result['email'],
        role=result['role'],
        region=result['region'],
        verified=result['verified'],
        pic_folder=result['pic_folder']
    )


async def get_user_role(user_id: str) -> str:
    """Get user's role."""
    async with get_async_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            result = await cur.fetchone()

    return result['role'] if result else None


async def create_user_from_whatsapp(phone: str, name: str, chat_id: str = None) -> str:
    """Create a new user from WhatsApp."""
    async with get_async_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("""
                INSERT INTO users (name, phone, whatsapp_number, whatsapp_chat_id, role, region, lang)
                VALUES (%s, %s, %s, %s, 'buyer', 'General', 'en')
                RETURNING id
            """, (name, phone, phone, chat_id))
            user_id = (await cur.fetchone())['id']
        await conn.commit()

    return str(user_id)


async def update_user_chat_id(user_id: str, chat_id: str):
    """Update user's WhatsApp chat_id if not already set."""
    async with get_async_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("""
                UPDATE users
                SET whatsapp_chat_id = %s
                WHERE id = %s AND whatsapp_chat_id IS NULL
            """, (chat_id, user_id))
        await conn.commit()


async def check_if_user_exist(phone: str) -> tuple:
    """Check if user exists by phone number."""
    async with get_async_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("""
                SELECT id FROM users
                WHERE phone = %s OR whatsapp_number = %s
            """, (phone, phone))
            result = await cur.fetchone()

    if result:
        return True, str(result['id'])
    return False, None


async def change_role_to_farmer(user_id: str, region: str) -> dict:
    """Change user role from buyer to farmer."""
    if region == "General":
        return {
            "status": "error",
            "message": (
                "⚠️ Farmers must select a specific region.\n\n"
                "'General' is for buyers who browse everywhere.\n"
                "As a farmer, choose your primary region of activity:\n"
                "Littoral, Centre, Ouest, Nord, Sud, etc."
            )
        }

    async with get_async_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("""
                UPDATE users
                SET role = 'farmer', region = %s
                WHERE id = %s
                RETURNING id
            """, (region, user_id))
            updated = await cur.fetchone()
        await conn.commit()

    if not updated:
        return {"status": "error", "message": "User not found"}

    return {
        "status": "ok",
        "message": f"✅ Role changed to Farmer in {region}\n\nYou can now create listings!"
    }


async def update_user_info(user_id: str, updates: dict) -> dict:
    """Update user profile information."""
    if not updates:
        return {"status": "error", "message": "Nothing to update"}

    fields = [f"{key} = %s" for key in updates.keys()]
    values = list(updates.values())
    values.extend([user_id])

    query = f"UPDATE users SET {', '.join(fields)}, updated_at = NOW() WHERE id = %s RETURNING id"

    async with get_async_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, values)
            updated = await cur.fetchone()
        await conn.commit()

    if not updated:
        return {"status": "error", "message": "User not found"}

    updated_fields = ", ".join(updates.keys())
    return {
        "status": "ok",
        "message": f"✅ Profile updated: {updated_fields}"
    }


async def update_verification_status(user_id: str, status: str, pic_folder: str = None) -> dict:
    """Update user's verification status."""
    async with get_async_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            if pic_folder:
                await cur.execute("""
                    UPDATE users
                    SET verified = %s, pic_folder = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                """, (status, pic_folder, user_id))
            else:
                await cur.execute("""
                    UPDATE users
                    SET verified = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                """, (status, user_id))
            updated = await cur.fetchone()
        await conn.commit()

    if not updated:
        return {"status": "error", "message": "User not found"}

    return {"status": "ok", "message": f"Verification status updated to: {status}"}
