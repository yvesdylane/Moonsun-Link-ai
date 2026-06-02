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

def clear_state(user_id: str):
    cur = conn.cursor()
    cur.execute("DELETE FROM conversation_state WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()