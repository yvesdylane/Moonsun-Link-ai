from db.connect import conn
from db.models.user import User


def get_all_users(page: int = 1, limit: int = 20, role: str = None,
                  verified: str = None, region: str = None, search: str = None) -> dict:
    conditions = []
    params = []

    if role:
        conditions.append("role = %s")
        params.append(role)
    if verified:
        conditions.append("verified = %s")
        params.append(verified)
    if region:
        conditions.append("region = %s")
        params.append(region)
    if search:
        conditions.append("(name ILIKE %s OR phone ILIKE %s OR whatsapp_number ILIKE %s OR telegram_number ILIKE %s)")
        q = f"%{search}%"
        params.extend([q, q, q, q])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    cur = conn.cursor()
    try:
        cur.execute(f"SELECT count(*) AS cnt FROM users {where}", params)
        total = cur.fetchone()["cnt"]

        offset = (page - 1) * limit
        cur.execute(f"""
            SELECT * FROM users {where}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        rows = cur.fetchall()

        users = [User.from_db_row(r) if r else None for r in rows]
        users = [u for u in users if u is not None]

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": max(1, -(-total // limit)),
            "users": [vars(u) for u in users],
        }
    finally:
        cur.close()


def get_all_listings(page: int = 1, limit: int = 20,
                     product_name: str = None, region: str = None,
                     verified_only: bool = False) -> dict:
    conditions = []
    params = []

    if product_name:
        conditions.append("p.name ILIKE %s")
        params.append(f"%{product_name}%")
    if region:
        conditions.append("(l.origin = %s OR loc.region = %s)")
        params.extend([region, region])
    if verified_only:
        conditions.append("u.verified = 'true'")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    cur = conn.cursor()
    try:
        count_query = f"""
            SELECT count(*) AS cnt
            FROM listings l
            JOIN products p ON l.product_id = p.id
            JOIN users u ON l.user_id = u.id
            LEFT JOIN locations loc ON l.location_id = loc.id
            {where}
        """
        cur.execute(count_query, params)
        total = cur.fetchone()["cnt"]

        offset = (page - 1) * limit
        query = f"""
            SELECT l.*, p.name AS product_name, u.name AS seller_name,
                   u.phone AS seller_phone, u.verified AS seller_verified,
                   loc.town, loc.region AS location_region
            FROM listings l
            JOIN products p ON l.product_id = p.id
            JOIN users u ON l.user_id = u.id
            LEFT JOIN locations loc ON l.location_id = loc.id
            {where}
            ORDER BY l.created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(query, params + [limit, offset])
        rows = cur.fetchall()

        listings = []
        for r in rows:
            d = dict(r)
            for k, v in d.items():
                if hasattr(v, 'isoformat'):
                    d[k] = v.isoformat()
            listings.append(d)

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": max(1, -(-total // limit)),
            "listings": listings,
        }
    finally:
        cur.close()


def get_dashboard_stats() -> dict:
    cur = conn.cursor()
    try:
        cur.execute("SELECT count(*) AS cnt FROM users")
        total_users = cur.fetchone()["cnt"]

        cur.execute("SELECT role, count(*) AS cnt FROM users GROUP BY role")
        role_rows = cur.fetchall()
        users_by_role = {r["role"]: r["cnt"] for r in role_rows}

        cur.execute("SELECT count(*) AS cnt FROM listings")
        total_listings = cur.fetchone()["cnt"]

        cur.execute("SELECT count(*) AS cnt FROM listing_interests")
        total_interests = cur.fetchone()["cnt"]

        cur.execute("SELECT count(*) AS cnt FROM users WHERE verified = 'pending'")
        pending_verifications = cur.fetchone()["cnt"]

        cur.execute("SELECT count(*) AS cnt FROM reports")
        total_reports = cur.fetchone()["cnt"]

        cur.execute("SELECT status, count(*) AS cnt FROM reports GROUP BY status")
        report_rows = cur.fetchall()
        reports_by_status = {r["status"]: r["cnt"] for r in report_rows}

        cur.execute("SELECT count(*) AS cnt FROM issues")
        total_issues = cur.fetchone()["cnt"]

        cur.execute("SELECT status, count(*) AS cnt FROM issues GROUP BY status")
        issue_rows = cur.fetchall()
        issues_by_status = {r["status"]: r["cnt"] for r in issue_rows}

        cur.execute("SELECT count(*) AS cnt FROM alerts")
        total_alerts = cur.fetchone()["cnt"]

        cur.execute("""
            SELECT origin, count(*) AS cnt
            FROM listings
            WHERE origin IS NOT NULL AND origin != 'General'
            GROUP BY origin
            ORDER BY cnt DESC
        """)
        region_rows = cur.fetchall()
        listings_by_region = {r["origin"]: r["cnt"] for r in region_rows}

        cur.execute("""
            SELECT count(*) AS cnt FROM message_logs
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        messages_24h = cur.fetchone()["cnt"]

        return {
            "total_users": total_users,
            "users_by_role": users_by_role,
            "total_listings": total_listings,
            "total_interests": total_interests,
            "pending_verifications": pending_verifications,
            "total_reports": total_reports,
            "reports_by_status": reports_by_status,
            "total_issues": total_issues,
            "issues_by_status": issues_by_status,
            "total_alerts": total_alerts,
            "listings_by_region": listings_by_region,
            "messages_last_24h": messages_24h,
        }
    finally:
        cur.close()


def get_pending_verifications() -> list[dict]:
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, user_id, name, phone, whatsapp_number, telegram_number,
                   telegram_id, whatsapp_chat_id, role, region, verified,
                   pic_folder, created_at
            FROM users
            WHERE verified = 'pending'
            ORDER BY updated_at DESC
        """)
        rows = cur.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["folder_url"] = d.get("pic_folder") or None
            for k, v in d.items():
                if hasattr(v, 'isoformat'):
                    d[k] = v.isoformat()
            results.append(d)
        return results
    finally:
        cur.close()


def approve_verification(user_id: str) -> dict:
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE users
            SET verified = 'true', updated_at = NOW()
            WHERE id = %s AND verified = 'pending'
            RETURNING id, name, whatsapp_chat_id, telegram_id
        """, (user_id,))
        row = cur.fetchone()
        conn.commit()
        if not row:
            return {"status": "error", "message": "User not found or not in pending verification"}
        return {
            "status": "ok",
            "message": f"User {row['name']} verified successfully",
            "user_id": str(row["id"]),
            "whatsapp_chat_id": row["whatsapp_chat_id"],
            "telegram_id": row["telegram_id"],
        }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()


def reject_verification(user_id: str) -> dict:
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE users
            SET verified = 'false', pic_folder = NULL, updated_at = NOW()
            WHERE id = %s AND verified = 'pending'
            RETURNING id, name, whatsapp_chat_id, telegram_id
        """, (user_id,))
        row = cur.fetchone()
        conn.commit()
        if not row:
            return {"status": "error", "message": "User not found or not in pending verification"}
        return {
            "status": "ok",
            "message": f"Verification rejected for {row['name']}",
            "user_id": str(row["id"]),
            "whatsapp_chat_id": row["whatsapp_chat_id"],
            "telegram_id": row["telegram_id"],
        }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()


def update_report_status(report_id: int, status: str) -> dict:
    valid = ("pending", "reviewed", "dismissed", "alert_created")
    if status not in valid:
        return {"status": "error", "message": f"Invalid status. Must be one of: {', '.join(valid)}"}
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE reports
            SET status = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, title, status
        """, (status, report_id))
        row = cur.fetchone()
        conn.commit()
        if not row:
            return {"status": "error", "message": "Report not found"}
        return {"status": "ok", "report": dict(row)}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()


def update_issue_status(issue_id: int, status: str) -> dict:
    valid = ("open", "resolved")
    if status not in valid:
        return {"status": "error", "message": f"Invalid status. Must be one of: {', '.join(valid)}"}
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE issues
            SET status = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, title, status
        """, (status, issue_id))
        row = cur.fetchone()
        conn.commit()
        if not row:
            return {"status": "error", "message": "Issue not found"}
        return {"status": "ok", "issue": dict(row)}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()
