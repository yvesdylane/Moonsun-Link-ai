from db.connect import conn
from entities.vocabulary import TYPE_DEFAULT_MEASUREMENTS


def get_product_id(product_name: str) -> int | None:
    """Direct lookup — product_name must be the exact name from Groq."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM products WHERE name = %s", (product_name,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def get_product_info(product_name: str) -> dict | None:
    """Direct lookup by exact name."""
    cur = conn.cursor()
    cur.execute("SELECT id, name, type, default_measurement FROM products WHERE name = %s", (product_name,))
    row = cur.fetchone()
    cur.close()
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "default_measurement": row[3],
        }
    return None


def create_product(name: str, product_type: str, default_measurement: str = None) -> int | None:
    """
    Create a new product in the database.

    Args:
        name: Product name (lowercase)
        product_type: One of 'crop', 'animal', 'tool', 'service'
        default_measurement: Default unit (auto-detected from type if None)

    Returns:
        The new product's id, or None on failure
    """
    name = name.strip().lower()
    if not default_measurement:
        default_measurement = TYPE_DEFAULT_MEASUREMENTS.get(product_type, "kg")

    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO products (name, type, default_measurement) VALUES (%s, %s, %s) RETURNING id",
            (name, product_type, default_measurement),
        )
        product_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        print(f"PRODUCT AUTO-CREATED: {name} (type={product_type}, measurement={default_measurement}, id={product_id})")
        return product_id
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"PRODUCT CREATE ERROR: {e}")
        return None
