from db.connect import conn
from db.controller.productController import get_product_id, get_product_info
from db.controller.userController import get_user_role
from entities.vocabulary import TYPE_DEFAULT_MEASUREMENTS


SERVICE_PRODUCT_TYPES = {"service"}


def create_listing(user_id, product_name, quantity, price, measurement=None,
                   town=None, region=None, origin=None, image_url=None):
    """
    Create a new listing.

    Auto-detects measurement from product info if not provided.
    Services expire in 1 year, everything else in 1 month.

    Returns dict with listing_id and missing_location flag.
    """
    info = get_product_info(product_name)
    if not info:
        return {"status": "error", "message": f"Product '{product_name}' not found"}

    product_id = info["id"]
    product_type = info["type"]

    # Auto-detect measurement
    if not measurement:
        measurement = info.get("default_measurement") or TYPE_DEFAULT_MEASUREMENTS.get(product_type, "kg")

    # Get user's region if not specified
    if not region:
        from db.controller.userController import get_user_info
        user = get_user_info(user_id)
        region = user.region if user else "General"

    # Use region as origin if origin not specified
    if not origin:
        origin = region

    # Determine expiry: services expire in 1 year
    if product_type == "service":
        expires_at = "NOW() + INTERVAL '1 year'"
    else:
        expires_at = "NOW() + INTERVAL '1 month'"

    cur = conn.cursor()
    query = f"""
        INSERT INTO listings (user_id, product_id, quantity, measurement, price, town, region, origin, image_url, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, {expires_at})
        RETURNING id
    """
    cur.execute(query, (user_id, product_id, quantity, measurement, price, town, region, origin, image_url))
    listing_id = cur.fetchone()[0]
    conn.commit()
    cur.close()

    return {
        "status": "ok",
        "listing_id": listing_id,
        "missing_location": town is None,
        "region": region,
        "product_name": product_name,
        "quantity": quantity,
        "measurement": measurement,
        "price": price,
    }


def delete_listing(listing_id: int, user_id: str):
    role = get_user_role(user_id)
    cur = conn.cursor()

    if role == "admin":
        cur.execute("DELETE FROM listings WHERE id = %s RETURNING id", (listing_id,))
    else:
        cur.execute("DELETE FROM listings WHERE id = %s AND user_id = %s RETURNING id", (listing_id, user_id))

    deleted = cur.fetchone()
    conn.commit()
    cur.close()

    if not deleted:
        return {"status": "error", "message": "Listing not found or not yours"}
    return {"status": "ok", "message": "Listing deleted"}


def update_listing(listing_id: int, user_id: str, updates: dict):
    if not updates:
        return {"status": "error", "message": "Nothing to update"}

    fields = [f"{key} = %s" for key in updates.keys()]
    values = list(updates.values())
    values.extend([listing_id, user_id])

    query = f"UPDATE listings SET {', '.join(fields)}, updated_at = NOW() WHERE id = %s AND user_id = %s RETURNING id"

    cur = conn.cursor()
    cur.execute(query, values)
    updated = cur.fetchone()
    conn.commit()
    cur.close()

    if not updated:
        return {"status": "error", "message": "Listing not found or not yours"}
    return {"status": "ok", "message": "Listing updated successfully"}


def get_listings(page=1, limit=10, product_name=None, town=None, region=None,
                 max_price=None, user_id=None, include_unverified=False,
                 listing_id=None, product_types=None):
    product_id = get_product_id(product_name) if product_name else None

    filters = []
    values = []

    if listing_id:
        filters.append("l.id = %s")
        values.append(listing_id)
    if product_id:
        filters.append("l.product_id = %s")
        values.append(product_id)
    if town:
        filters.append("l.town ILIKE %s")
        values.append(f"%{town}%")
    if region:
        filters.append("(l.region = %s OR l.region = 'General')")
        values.append(region)
    if max_price:
        filters.append("l.price <= %s")
        values.append(max_price)
    if user_id:
        filters.append("l.user_id = %s")
        values.append(user_id)
    else:
        if not include_unverified:
            filters.append("u.verified = 'true'")

    # Product type filter: default to crops+animals for public search
    if product_types is not None:
        if len(product_types) == 1:
            filters.append("p.type = %s")
            values.append(product_types[0])
        else:
            placeholders = ",".join(["%s"] * len(product_types))
            filters.append(f"p.type IN ({placeholders})")
            values.extend(product_types)
    elif not user_id and not product_id:
        # Public search without a specific product: show crops + animals
        filters.append("p.type IN ('crop', 'animal')")

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    offset = (page - 1) * limit

    cur = conn.cursor()

    cur.execute(f"""
        SELECT COUNT(*)
        FROM listings l
        JOIN products p ON l.product_id = p.id
        JOIN users u ON l.user_id = u.id
        {where}
    """, values)
    total = cur.fetchone()[0]

    cur.execute(f"""
        SELECT l.*, p.name as product_name, u.name as seller_name
        FROM listings l
        JOIN products p ON l.product_id = p.id
        JOIN users u ON l.user_id = u.id
        {where}
        ORDER BY l.created_at DESC
        LIMIT %s OFFSET %s
    """, values + [limit, offset])

    listings = cur.fetchall()
    cur.close()

    total_pages = (total + limit - 1) // limit

    return {
        "listings": listings,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


def get_available_products() -> list:
    """
    Get list of distinct products currently being sold by verified farmers.

    Returns:
        List of product names (all types except services)
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT p.name
        FROM listings l
        JOIN products p ON l.product_id = p.id
        JOIN users u ON l.user_id = u.id
        WHERE u.verified = 'true'
          AND p.type != 'service'
        ORDER BY p.name
    """)
    products = [row[0] for row in cur.fetchall()]
    cur.close()
    return products


def get_product_locations(product_name: str) -> dict:
    """
    Get regions and towns where a specific product is being sold by verified farmers.

    Args:
        product_name: Name of the product

    Returns:
        dict with status, product name, and location data
    """
    info = get_product_info(product_name)
    if not info:
        return {"status": "error", "message": f"Product '{product_name}' not recognized"}

    product_id = info["id"]

    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.product_id = %s AND u.verified = 'true'
    """, (product_id,))

    count = cur.fetchone()[0]

    if count == 0:
        cur.close()
        return {
            "status": "not_found",
            "product": product_name,
            "message": f"No one is currently selling {product_name}",
        }

    cur.execute("""
        SELECT DISTINCT l.region, l.town
        FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.product_id = %s AND u.verified = 'true'
        ORDER BY l.region, l.town
    """, (product_id,))

    locations = cur.fetchall()
    cur.close()

    regions_data = {}
    for region, town in locations:
        if region not in regions_data:
            regions_data[region] = []
        if town and town not in regions_data[region]:
            regions_data[region].append(town)

    return {
        "status": "ok",
        "product": product_name,
        "count": count,
        "regions": regions_data,
    }


def check_product_exists(product_name: str, region: str = None, max_price: int = None) -> dict:
    """
    Check if a product exists in verified listings and where it fails criteria.

    Args:
        product_name: Name of the product
        region: Optional region filter
        max_price: Optional maximum price filter

    Returns:
        dict with existence status and alternative suggestions
    """
    info = get_product_info(product_name)
    if not info:
        return {"exists": False, "reason": "unknown_product"}

    product_id = info["id"]

    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.product_id = %s AND u.verified = 'true'
    """, (product_id,))

    total_count = cur.fetchone()[0]

    if total_count == 0:
        cur.close()
        return {"exists": False, "reason": "not_listed"}

    filters = ["l.product_id = %s", "u.verified = 'true'"]
    values = [product_id]

    if region:
        filters.append("l.region = %s")
        values.append(region)

    if max_price:
        filters.append("l.price <= %s")
        values.append(max_price)

    where = " AND ".join(filters)

    cur.execute(f"""
        SELECT COUNT(*)
        FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE {where}
    """, values)

    filtered_count = cur.fetchone()[0]

    if filtered_count > 0:
        cur.close()
        return {"exists": True, "count": filtered_count}

    feedback = {"exists": True, "matches_criteria": False, "total_listings": total_count}

    if region:
        cur.execute("""
            SELECT DISTINCT l.region
            FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.product_id = %s AND u.verified = 'true'
        """, (product_id,))
        available_regions = [row[0] for row in cur.fetchall()]
        feedback["available_regions"] = available_regions
        feedback["searched_region"] = region

    if max_price:
        cur.execute("""
            SELECT MIN(l.price)
            FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.product_id = %s AND u.verified = 'true'
        """, (product_id,))
        min_price = cur.fetchone()[0]
        feedback["min_price"] = min_price
        feedback["max_price_searched"] = max_price

    cur.close()
    return feedback


def search_by_price(product_name: str, target_price: int, tolerance_percent: float = 15.0) -> dict:
    """
    Search for listings at or near a specific price point.

    Args:
        product_name: Name of the product
        target_price: Desired price per unit
        tolerance_percent: Price tolerance as percentage (default: 15%)

    Returns:
        dict with exact matches or nearest alternatives
    """
    from db.controller.productController import get_product_id, get_product_info
    from utils.price_helper import calculate_price_range

    info = get_product_info(product_name)
    if not info:
        return {"status": "error", "message": f"Product '{product_name}' not recognized"}

    product_id = info["id"]

    min_price, max_price = calculate_price_range(target_price, tolerance_percent)

    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.product_id = %s AND u.verified = 'true'
    """, (product_id,))

    total_count = cur.fetchone()[0]

    if total_count == 0:
        cur.close()
        return {
            "status": "not_found",
            "message": f"No one is currently selling {product_name}",
        }

    cur.execute("""
        SELECT l.*, p.name as product_name, u.name as seller_name,
               ABS(l.price - %s) as price_diff
        FROM listings l
        JOIN products p ON l.product_id = p.id
        JOIN users u ON l.user_id = u.id
        WHERE l.product_id = %s
          AND u.verified = 'true'
          AND l.price BETWEEN %s AND %s
        ORDER BY price_diff ASC, l.created_at DESC
        LIMIT 10
    """, (target_price, product_id, min_price, max_price))

    close_matches = cur.fetchall()

    if close_matches:
        cur.close()
        return {
            "status": "ok",
            "match_type": "close",
            "target_price": target_price,
            "tolerance_percent": tolerance_percent,
            "price_range": (min_price, max_price),
            "listings": close_matches,
            "message": f"Found {len(close_matches)} listing(s) near {target_price} XAF",
        }

    cur.execute("""
        SELECT l.price, COUNT(*) as count
        FROM listings l
        JOIN users u ON l.user_id = u.id
        WHERE l.product_id = %s AND u.verified = 'true'
        GROUP BY l.price
        ORDER BY ABS(l.price - %s) ASC
        LIMIT 3
    """, (product_id, target_price))

    nearest_prices = cur.fetchall()
    cur.close()

    return {
        "status": "alternatives",
        "target_price": target_price,
        "nearest_prices": [{"price": row[0], "count": row[1]} for row in nearest_prices],
        "message": f"No listings at {target_price} XAF, but here are the nearest prices",
    }
