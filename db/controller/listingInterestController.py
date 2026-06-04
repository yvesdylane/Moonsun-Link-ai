from psycopg.rows import dict_row

from db.connect import conn


def save_interest(listing_id: int, user_id: str, quantity: int = None, message: str = None) -> dict:
    """
    Save a user's interest in a listing.

    Args:
        listing_id: ID of the listing
        user_id: ID of the interested user
        quantity: Optional quantity user is interested in
        message: Optional message to seller

    Returns:
        dict with status, buyer info (for farmer notification), and listing info
    """
    cur = conn.cursor(row_factory=dict_row)

    cur.execute("""
        SELECT l.id, l.user_id, l.product_id, l.quantity, l.measurement, l.price,
               loc.town, loc.region, l.origin, l.image_url,
               l.expires_at, l.created_at, l.updated_at,
               p.name as product_name, u.name as seller_name,
               u.whatsapp_chat_id as seller_whatsapp_chat_id,
               u.telegram_id as seller_telegram_id
        FROM listings l
        JOIN products p ON l.product_id = p.id
        JOIN users u ON l.user_id = u.id
        LEFT JOIN locations loc ON l.location_id = loc.id
        WHERE l.id = %s AND u.verified = 'true'
    """, (listing_id,))

    listing_data = cur.fetchone()

    if not listing_data:
        cur.close()
        return {"status": "error", "message": "Listing not found or no longer available"}

    if str(listing_data['user_id']) == str(user_id):
        cur.close()
        return {"status": "error", "message": "You cannot show interest in your own listing"}

    cur.execute("""
        SELECT name, phone, whatsapp_chat_id
        FROM users
        WHERE id = %s
    """, (user_id,))
    buyer_info = cur.fetchone()

    cur.execute("""
        SELECT id FROM listing_interests
        WHERE listing_id = %s AND user_id = %s AND status = 'active'
    """, (listing_id, user_id))

    existing_interest = cur.fetchone()

    try:
        if existing_interest:
            cur.execute("""
                UPDATE listing_interests
                SET interested_quantity = %s, message = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING id
            """, (quantity, message, existing_interest['id']))
            interest_id = cur.fetchone()['id']
        else:
            cur.execute("""
                INSERT INTO listing_interests (listing_id, user_id, interested_quantity, message, status)
                VALUES (%s, %s, %s, %s, 'active')
                RETURNING id
            """, (listing_id, user_id, quantity, message))
            interest_id = cur.fetchone()['id']

        conn.commit()
        cur.close()

        return {
            "status": "ok",
            "interest_id": interest_id,
            "listing": {
                "id": listing_data['id'],
                "product_name": listing_data['product_name'],
                "quantity": listing_data['quantity'],
                "measurement": listing_data['measurement'],
                "price": listing_data['price'],
                "seller_name": listing_data['seller_name'],
            },
            "buyer": {
                "name": buyer_info['name'],
                "phone": buyer_info['phone'],
            },
            "seller_notification": {
                "seller_whatsapp_chat_id": listing_data['seller_whatsapp_chat_id'],
                "seller_telegram_id": listing_data['seller_telegram_id'],
                "buyer_name": buyer_info['name'],
                "buyer_phone": buyer_info['phone'],
                "product_name": listing_data['product_name'],
                "quantity": quantity,
            },
        }
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"SAVE INTEREST ERROR: {e}")
        return {"status": "error", "message": "Failed to save interest. Please try again."}


def get_listing_interests(user_id: str, product_name: str = None) -> dict:
    """
    Get active interests shown on a farmer's listings (last 3 months).

    Args:
        user_id: Farmer's user ID
        product_name: Optional filter by product name

    Returns:
        dict with interests grouped by listing
    """
    cur = conn.cursor(row_factory=dict_row)

    filters = ["l.user_id = %s", "li.status = 'active'", "li.created_at >= NOW() - INTERVAL '3 months'"]
    values = [user_id]

    if product_name:
        from db.controller.productController import get_product_id
        product_id = get_product_id(product_name)
        if product_id:
            filters.append("l.product_id = %s")
            values.append(product_id)

    where_clause = " AND ".join(filters)

    cur.execute(f"""
        SELECT
            li.id,
            l.id as listing_id,
            p.name as product_name,
            l.quantity,
            l.price,
            li.interested_quantity,
            li.message,
            u.name as buyer_name,
            u.phone as buyer_phone,
            li.created_at,
            li.status
        FROM listing_interests li
        JOIN listings l ON li.listing_id = l.id
        JOIN products p ON l.product_id = p.id
        JOIN users u ON li.user_id = u.id
        WHERE {where_clause}
        ORDER BY li.created_at DESC
    """, values)

    interests = cur.fetchall()
    cur.close()

    if not interests:
        return {
            "status": "ok",
            "total": 0,
            "message": "No one has shown interest in your listings yet.",
        }

    grouped = {}
    for interest in interests:
        listing_id = interest['listing_id']
        if listing_id not in grouped:
            grouped[listing_id] = {
                "product_name": interest['product_name'],
                "quantity": interest['quantity'],
                "price": interest['price'],
                "interests": [],
            }

        grouped[listing_id]["interests"].append({
            "interest_id": interest['id'],
            "quantity": interest['interested_quantity'],
            "message": interest['message'],
            "buyer_name": interest['buyer_name'],
            "buyer_phone": interest['buyer_phone'],
            "created_at": interest['created_at'],
            "status": interest['status'],
        })

    return {
        "status": "ok",
        "total": len(interests),
        "listings": grouped,
    }


def get_user_interests(user_id: str) -> dict:
    """
    Get all active interests a user has shown (buyer's view, last 3 months).

    Args:
        user_id: Buyer's user ID

    Returns:
        dict with user's interests
    """
    cur = conn.cursor(row_factory=dict_row)

    cur.execute("""
        SELECT
            li.id,
            l.id as listing_id,
            p.name as product_name,
            l.quantity,
            l.price,
            li.interested_quantity,
            li.message,
            u.name as seller_name,
            li.created_at,
            li.status
        FROM listing_interests li
        JOIN listings l ON li.listing_id = l.id
        JOIN products p ON l.product_id = p.id
        JOIN users u ON l.user_id = u.id
        WHERE li.user_id = %s
          AND li.status = 'active'
          AND li.created_at >= NOW() - INTERVAL '3 months'
        ORDER BY li.created_at DESC
    """, (user_id,))

    interests = cur.fetchall()
    cur.close()

    if not interests:
        return {
            "status": "ok",
            "total": 0,
            "message": "You haven't shown interest in any listings yet.",
        }

    formatted_interests = []
    for interest in interests:
        formatted_interests.append({
            "interest_id": interest['id'],
            "listing_id": interest['listing_id'],
            "product_name": interest['product_name'],
            "listing_quantity": interest['quantity'],
            "price": interest['price'],
            "interested_quantity": interest['interested_quantity'],
            "message": interest['message'],
            "seller_name": interest['seller_name'],
            "created_at": interest['created_at'],
            "status": interest['status'],
        })

    return {
        "status": "ok",
        "total": len(interests),
        "interests": formatted_interests,
    }


def cancel_interest(interest_id: int, user_id: str) -> dict:
    """
    Cancel an interest (buyer cancels their own interest).

    Args:
        interest_id: ID of the interest
        user_id: ID of the buyer (to verify ownership)

    Returns:
        dict with status and farmer notification data
    """
    cur = conn.cursor(row_factory=dict_row)

    cur.execute("""
        SELECT li.id, li.listing_id, li.user_id, li.status,
               l.user_id as farmer_id, p.name as product_name,
               u.whatsapp_chat_id as farmer_chat_id, u.name as farmer_name,
               buyer.name as buyer_name
        FROM listing_interests li
        JOIN listings l ON li.listing_id = l.id
        JOIN products p ON l.product_id = p.id
        JOIN users u ON l.user_id = u.id
        JOIN users buyer ON li.user_id = buyer.id
        WHERE li.id = %s
    """, (interest_id,))

    interest_data = cur.fetchone()

    if not interest_data:
        cur.close()
        return {"status": "error", "message": "Interest not found"}

    if str(interest_data['user_id']) != str(user_id):
        cur.close()
        return {"status": "error", "message": "You can only cancel your own interests"}

    if interest_data['status'] != 'active':
        cur.close()
        return {"status": "error", "message": "This interest is already cancelled or rejected"}

    try:
        cur.execute("""
            UPDATE listing_interests
            SET status = 'cancelled_by_buyer', updated_at = NOW()
            WHERE id = %s
        """, (interest_id,))
        conn.commit()
        cur.close()

        return {
            "status": "ok",
            "message": f"Interest in {interest_data['product_name']} cancelled successfully",
            "farmer_notification": {
                "farmer_chat_id": interest_data['farmer_chat_id'],
                "buyer_name": interest_data['buyer_name'],
                "product_name": interest_data['product_name'],
            },
        }
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"CANCEL INTEREST ERROR: {e}")
        return {"status": "error", "message": "Failed to cancel interest"}


def reject_interest(interest_id: int, farmer_id: str) -> dict:
    """
    Reject an interest (farmer rejects a buyer's interest).

    Args:
        interest_id: ID of the interest
        farmer_id: ID of the farmer (to verify ownership of listing)

    Returns:
        dict with status and buyer notification data
    """
    cur = conn.cursor(row_factory=dict_row)

    cur.execute("""
        SELECT li.id, li.listing_id, li.user_id, li.status,
               l.user_id as farmer_id, p.name as product_name,
               u.whatsapp_chat_id as buyer_chat_id, u.name as buyer_name,
               farmer.name as farmer_name
        FROM listing_interests li
        JOIN listings l ON li.listing_id = l.id
        JOIN products p ON l.product_id = p.id
        JOIN users u ON li.user_id = u.id
        JOIN users farmer ON l.user_id = farmer.id
        WHERE li.id = %s
    """, (interest_id,))

    interest_data = cur.fetchone()

    if not interest_data:
        cur.close()
        return {"status": "error", "message": "Interest not found"}

    if str(interest_data['farmer_id']) != str(farmer_id):
        cur.close()
        return {"status": "error", "message": "You can only reject interests on your own listings"}

    if interest_data['status'] != 'active':
        cur.close()
        return {"status": "error", "message": "This interest is already cancelled or rejected"}

    try:
        cur.execute("""
            UPDATE listing_interests
            SET status = 'rejected_by_farmer', updated_at = NOW()
            WHERE id = %s
        """, (interest_id,))
        conn.commit()
        cur.close()

        return {
            "status": "ok",
            "message": f"Interest from {interest_data['buyer_name']} rejected",
            "buyer_notification": {
                "buyer_chat_id": interest_data['buyer_chat_id'],
                "farmer_name": interest_data['farmer_name'],
                "product_name": interest_data['product_name'],
            },
        }
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"REJECT INTEREST ERROR: {e}")
        return {"status": "error", "message": "Failed to reject interest"}


def get_all_interests(status: str = None, listing_id: int = None,
                      user_id: str = None) -> list[dict]:
    """Admin view: list all listing interests with filters."""
    cur = conn.cursor(row_factory=dict_row)
    try:
        conditions = []
        values = []
        if status:
            conditions.append("li.status = %s")
            values.append(status)
        if listing_id:
            conditions.append("li.listing_id = %s")
            values.append(listing_id)
        if user_id:
            conditions.append("li.user_id = %s")
            values.append(user_id)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        cur.execute(f"""
            SELECT li.*, p.name AS product_name,
                   buyer.name AS buyer_name, buyer.phone AS buyer_phone,
                   seller.name AS seller_name, seller.phone AS seller_phone
            FROM listing_interests li
            JOIN listings l ON li.listing_id = l.id
            JOIN products p ON l.product_id = p.id
            JOIN users buyer ON li.user_id = buyer.id
            JOIN users seller ON l.user_id = seller.id
            {where}
            ORDER BY li.created_at DESC
        """, values)
        return cur.fetchall()
    finally:
        cur.close()
