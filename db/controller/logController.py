from db.connect import conn
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