from db.connect import conn
from psycopg.rows import dict_row
import json

def log_message(input_text: str, intent: dict, entities: dict):
    cur = conn.cursor()
    query = """
        INSERT INTO assistant_logs (input_text, intent, confidence, method, entities)
        VALUES (%s, %s, %s, %s, %s)
    """
    cur.execute(query, (
        input_text,
        intent["intent"],
        intent["confidence"],
        intent["method"],
        json.dumps(entities)
    ))
    conn.commit()
    cur.close()


def get_assistant_logs(intent: str = None, method: str = None) -> list[dict]:
    cur = conn.cursor(row_factory=dict_row)
    try:
        conditions = []
        values = []
        if intent:
            conditions.append("intent = %s")
            values.append(intent)
        if method:
            conditions.append("method = %s")
            values.append(method)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        cur.execute(f"""
            SELECT * FROM assistant_logs {where} ORDER BY timestamp DESC
        """, values)
        return cur.fetchall()
    finally:
        cur.close()


def get_assistant_log(log_id: int) -> dict | None:
    cur = conn.cursor(row_factory=dict_row)
    try:
        cur.execute("SELECT * FROM assistant_logs WHERE id = %s", (log_id,))
        return cur.fetchone()
    finally:
        cur.close()