from db.connect import conn


def create_advice(title: str, content: str, author_id: str,
                  issue_id: int = None, product_name: str = None,
                  issue_type: str = None, is_verified: bool = False) -> dict:
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO advice (title, content, author_id, issue_id,
                                product_name, issue_type, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (title, content, author_id, issue_id, product_name, issue_type, is_verified))
        advice = cur.fetchone()
        conn.commit()
        if not advice:
            return {"status": "error", "message": "Failed to create advice"}
        return {"status": "ok", "advice": advice}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()


def get_advice(advice_id: int) -> dict | None:
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT a.*, u.name AS author_name
            FROM advice a
            JOIN users u ON a.author_id = u.id
            WHERE a.id = %s
        """, (advice_id,))
        return cur.fetchone()
    finally:
        cur.close()


def get_all_advice(product_name: str = None, issue_type: str = None,
                   is_verified: bool = None) -> list[dict]:
    cur = conn.cursor()
    try:
        conditions = []
        params = []
        if product_name:
            conditions.append("a.product_name = %s")
            params.append(product_name)
        if issue_type:
            conditions.append("a.issue_type = %s")
            params.append(issue_type)
        if is_verified is not None:
            conditions.append("a.is_verified = %s")
            params.append(is_verified)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cur.execute(f"""
            SELECT a.*, u.name AS author_name
            FROM advice a
            JOIN users u ON a.author_id = u.id
            {where}
            ORDER BY a.created_at DESC
        """, params)
        return cur.fetchall()
    finally:
        cur.close()


def update_advice(advice_id: int, updates: dict) -> dict:
    if not updates:
        return {"status": "error", "message": "Nothing to update"}

    fields = [f"{key} = %s" for key in updates.keys()]
    values = list(updates.values())
    values.append(advice_id)

    cur = conn.cursor()
    try:
        cur.execute(f"""
            UPDATE advice
            SET {', '.join(fields)}, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """, values)
        updated = cur.fetchone()
        conn.commit()
        if not updated:
            return {"status": "error", "message": "Advice not found"}
        return {"status": "ok", "advice": updated}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()


def delete_advice(advice_id: int) -> dict:
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM advice WHERE id = %s
            RETURNING id
        """, (advice_id,))
        deleted = cur.fetchone()
        conn.commit()
        if not deleted:
            return {"status": "error", "message": "Advice not found"}
        return {"status": "ok", "message": "Advice deleted"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()
