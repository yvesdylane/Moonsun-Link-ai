from db.connect import conn


def create_report(user_id: str, report_type: str, title: str,
                  description: str = None, product_name: str = None,
                  location: str = None, region: str = None) -> dict:
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO reports (user_id, report_type, title, description, product_name, location, region)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (user_id, report_type, title, description, product_name, location, region))
        report_id, created_at = cur.fetchone()
        conn.commit()
        return {
            "status": "ok",
            "report_id": report_id,
            "report_type": report_type,
            "title": title,
            "created_at": created_at,
        }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": f"Failed to create report: {e}"}
    finally:
        cur.close()


def get_reports(status: str = None, user_id: str = None) -> list:
    filters = []
    values = []
    if status:
        filters.append("r.status = %s")
        values.append(status)
    if user_id:
        filters.append("r.user_id = %s")
        values.append(user_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    cur = conn.cursor()
    cur.execute(f"""
        SELECT r.*, u.name as user_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        {where}
        ORDER BY r.created_at DESC
    """, values)
    rows = cur.fetchall()
    cur.close()
    return rows


def get_active_alerts(region: str = None) -> list:
    cur = conn.cursor()
    if region:
        cur.execute("""
            SELECT id, title, description, alert_type, region, product_name, created_at, expires_at
            FROM alerts
            WHERE (region IS NULL OR region = %s OR region = 'General')
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
        """, (region,))
    else:
        cur.execute("""
            SELECT id, title, description, alert_type, region, product_name, created_at, expires_at
            FROM alerts
            WHERE expires_at IS NULL OR expires_at > NOW()
            ORDER BY created_at DESC
        """)
    rows = cur.fetchall()
    cur.close()
    return rows
