from db.connect import conn

def log_message_exchange(user_id: str, incoming: str, outgoing: str, intent: str, platform: str = "whatsapp"):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO message_logs (user_id, platform, incoming_message, outgoing_reply, intent)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, platform, incoming, outgoing, intent))
    conn.commit()
    cur.close()