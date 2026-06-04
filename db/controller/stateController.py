from db.connect import conn
import json
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

def get_state(user_id: str) -> dict | None:
    cur = conn.cursor(row_factory=dict_row)
    cur.execute("SELECT state, context FROM conversation_state WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    if result:
        return {"state": result['state'], "context": result['context'] if result['context'] else {}}
    return None

def set_state(user_id: str, state: str, context: dict = {}):
    cur = conn.cursor(row_factory=dict_row)
    cur.execute("SELECT id FROM conversation_state WHERE user_id = %s", (user_id,))
    exists = cur.fetchone()
    if exists:
        cur.execute("""
            UPDATE conversation_state SET state = %s, context = %s, updated_at = NOW()
            WHERE user_id = %s
        """, (state, Jsonb(context), user_id))
    else:
        cur.execute("""
            INSERT INTO conversation_state (user_id, state, context)
            VALUES (%s, %s, %s)
        """, (user_id, state, Jsonb(context)))
    conn.commit()
    cur.close()

def get_all_conversation_states(state: str = None) -> list[dict]:
    cur = conn.cursor(row_factory=dict_row)
    try:
        if state:
            cur.execute("""
                SELECT cs.*, u.name AS user_name, u.phone AS user_phone
                FROM conversation_state cs
                JOIN users u ON cs.user_id = u.id
                WHERE cs.state = %s
                ORDER BY cs.updated_at DESC
            """, (state,))
        else:
            cur.execute("""
                SELECT cs.*, u.name AS user_name, u.phone AS user_phone
                FROM conversation_state cs
                JOIN users u ON cs.user_id = u.id
                ORDER BY cs.updated_at DESC
            """)
        return cur.fetchall()
    finally:
        cur.close()


def get_conversation_state_detail(state_id: int) -> dict | None:
    cur = conn.cursor(row_factory=dict_row)
    try:
        cur.execute("""
            SELECT cs.*, u.name AS user_name, u.phone AS user_phone
            FROM conversation_state cs
            JOIN users u ON cs.user_id = u.id
            WHERE cs.id = %s
        """, (state_id,))
        return cur.fetchone()
    finally:
        cur.close()


def clear_state(user_id: str):
    cur = conn.cursor()
    cur.execute("DELETE FROM conversation_state WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()