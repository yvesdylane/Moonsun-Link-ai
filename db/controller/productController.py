from db.connect import conn
from rapidfuzz import process, fuzz
from entities.vocabulary import PRODUCT_SYNONYMS, PRODUCT_TYPES, TYPE_DEFAULT_MEASUREMENTS


def get_product_id(product_name: str) -> int | None:
    """Look up a product by name, return its id (or None)."""
    name = PRODUCT_SYNONYMS.get(product_name.lower(), product_name)

    cur = conn.cursor()
    cur.execute("SELECT id, name FROM products")
    products = cur.fetchall()
    cur.close()

    names = [row[1] for row in products]
    match = process.extractOne(name, names, scorer=fuzz.ratio)

    if match and match[1] >= 70:
        matched_name = match[0]
        for row in products:
            if row[1] == matched_name:
                return row[0]

    return None


def get_product_info(product_name: str) -> dict | None:
    """
    Look up a product by name, return full info.

    Returns:
        {"id": int, "name": str, "type": str, "default_measurement": str}
        or None if not found
    """
    name = PRODUCT_SYNONYMS.get(product_name.lower(), product_name)

    cur = conn.cursor()
    cur.execute("SELECT id, name, type, default_measurement FROM products")
    products = cur.fetchall()
    cur.close()

    names = [row[1] for row in products]
    match = process.extractOne(name, names, scorer=fuzz.ratio)

    if match and match[1] >= 70:
        matched_name = match[0]
        for row in products:
            if row[1] == matched_name:
                return {
                    "id": row[0],
                    "name": row[1],
                    "type": row[2],
                    "default_measurement": row[3],
                }

    return None
