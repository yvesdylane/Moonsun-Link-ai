from db.connect import conn
from db.controller.productController import get_product_id, get_product_info


def get_product_price(product_name: str, region: str = None) -> dict:
    """
    Get price data for a product in specific region or all regions.

    Args:
        product_name: Name of the product
        region: Optional specific region

    Returns:
        dict with status, product info, and price data
    """
    # Services don't have reliable market prices
    info = get_product_info(product_name)
    if info and info["type"] == "service":
        return {
            "status": "service_not_supported",
            "product_name": product_name,
            "message": (
                f"⚠️ We cannot provide market prices for '{product_name}' "
                "because service prices vary based on provider standards, "
                "experience, and specific job requirements.\n\n"
                "To find service providers, search for listings instead."
            )
        }

    product_id = get_product_id(product_name)
    if not product_id:
        return {
            "status": "error",
            "message": f"Product '{product_name}' not found."
        }

    cur = conn.cursor()

    if region:
        cur.execute("""
            SELECT region, min_price, max_price, avg_price
            FROM product_prices
            WHERE product_id = %s AND region = %s
        """, (product_id, region))

        result = cur.fetchone()
        cur.close()

        if not result:
            return {
                "status": "ok",
                "product_name": product_name,
                "region": region,
                "overall_avg": None,
                "prices": [],
                "message": f"No price data available for '{product_name}' in {region}."
            }

        return {
            "status": "ok",
            "product_name": product_name,
            "region": region,
            "overall_avg": result['avg_price'],
            "prices": [{
                "region": result['region'],
                "min": result['min_price'],
                "max": result['max_price'],
                "avg": result['avg_price']
            }]
        }

    # Get all regions
    cur.execute("""
        SELECT region, min_price, max_price, avg_price
        FROM product_prices
        WHERE product_id = %s
        ORDER BY region
    """, (product_id,))

    prices = cur.fetchall()
    cur.close()

    if not prices:
        return {
            "status": "ok",
            "product_name": product_name,
            "overall_avg": None,
            "prices": [],
            "message": f"No price data available for '{product_name}'."
        }

    # Calculate overall average
    total_avg = sum(row['avg_price'] for row in prices)
    overall_avg = total_avg // len(prices)

    return {
        "status": "ok",
        "product_name": product_name,
        "overall_avg": overall_avg,
        "prices": [
            {
                "region": row['region'],
                "min": row['min_price'],
                "max": row['max_price'],
                "avg": row['avg_price']
            }
            for row in prices
        ]
    }


def get_all_product_prices() -> dict:
    """
    Get price overview for all products (excludes services).

    Returns:
        dict with product list
    """
    cur = conn.cursor()
    # Get all non-service products that have prices
    cur.execute("""
        SELECT p.id, p.name
        FROM products p
        JOIN product_prices pp ON p.id = pp.product_id
        WHERE p.type != 'service'
        GROUP BY p.id, p.name
        ORDER BY p.name
    """)
    products = cur.fetchall()
    cur.close()

    result_products = []
    for product in products:
        price_data = get_product_price(product['name'])
        if price_data["status"] == "ok" and price_data.get("prices"):
            min_price = min(p["min"] for p in price_data["prices"])
            max_price = max(p["max"] for p in price_data["prices"])
            result_products.append({
                "product_name": product['name'],
                "overall_avg": price_data["overall_avg"],
                "min_price": min_price,
                "max_price": max_price,
            })

    return {
        "status": "ok",
        "products": result_products
    }


def get_market_price_for_listing_search(product_name: str = None, region: str = None) -> dict:
    """
    Get market price for listing search context.
    Adds a header showing average price when browsing listings.

    Args:
        product_name: Optional product name
        region: Optional region

    Returns:
        dict with status and price info, or None if not applicable
    """
    if not product_name:
        return None

    # Services don't get market price headers
    info = get_product_info(product_name)
    if info and info["type"] == "service":
        return None

    product_id = get_product_id(product_name)
    if not product_id:
        return None

    cur = conn.cursor()

    if region:
        cur.execute("""
            SELECT min_price, max_price, avg_price
            FROM product_prices
            WHERE product_id = %s AND region = %s
        """, (product_id, region))
        result = cur.fetchone()
        cur.close()

        if result:
            return {
                "product_name": product_name,
                "region": region,
                "min_price": result['min_price'],
                "max_price": result['max_price'],
                "avg_price": result['avg_price'],
            }
        return None

    # Overall average across all regions
    cur.execute("""
        SELECT AVG(avg_price)::INTEGER AS avg_price
        FROM product_prices
        WHERE product_id = %s
    """, (product_id,))
    result = cur.fetchone()
    cur.close()

    if result and result['avg_price']:
        return {
            "product_name": product_name,
            "avg_price": result['avg_price'],
        }

    return None


def calculate_overall_avg(product_id: int) -> float:
    """Calculate overall average price for a product across all regions."""
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(avg_price) AS avg_price
        FROM product_prices
        WHERE product_id = %s
    """, (product_id,))
    result = cur.fetchone()
    cur.close()
    return result['avg_price'] if result and result['avg_price'] else None
