from db.connect import conn
from entities.vocabulary import TYPE_DEFAULT_MEASUREMENTS


def get_product_id(product_name: str) -> int | None:
    """Direct lookup — product_name must be the exact name from Groq."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM products WHERE name = %s", (product_name,))
    row = cur.fetchone()
    cur.close()
    return row['id'] if row else None


def get_product_info(product_name: str) -> dict | None:
    """Direct lookup by exact name."""
    cur = conn.cursor()
    cur.execute("SELECT id, name, type, default_measurement FROM products WHERE name = %s", (product_name,))
    row = cur.fetchone()
    cur.close()
    if row:
        return {
            "id": row['id'],
            "name": row['name'],
            "type": row['type'],
            "default_measurement": row['default_measurement'],
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
        product_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        print(f"PRODUCT AUTO-CREATED: {name} (type={product_type}, measurement={default_measurement}, id={product_id})")
        return product_id
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"PRODUCT CREATE ERROR: {e}")
        return None


def get_all_products(product_type: str = None) -> list[dict]:
    cur = conn.cursor()
    try:
        if product_type:
            cur.execute("""
                SELECT * FROM products WHERE type = %s ORDER BY name
            """, (product_type,))
        else:
            cur.execute("""
                SELECT * FROM products ORDER BY name
            """)
        return cur.fetchall()
    finally:
        cur.close()


def update_product(product_id: int, updates: dict) -> dict:
    if not updates:
        return {"status": "error", "message": "Nothing to update"}

    fields = [f"{key} = %s" for key in updates.keys()]
    values = list(updates.values())
    values.append(product_id)

    cur = conn.cursor()
    try:
        cur.execute(f"""
            UPDATE products
            SET {', '.join(fields)}, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """, values)
        updated = cur.fetchone()
        conn.commit()
        if not updated:
            return {"status": "error", "message": "Product not found"}
        return {"status": "ok", "product": updated}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()


def delete_product(product_id: int) -> dict:
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) AS cnt FROM listings WHERE product_id = %s", (product_id,))
        count = cur.fetchone()["cnt"]
        if count > 0:
            return {
                "status": "error",
                "message": f"Cannot delete: {count} listing(s) still reference this product. Remove or reassign them first."
            }

        cur.execute("DELETE FROM products WHERE id = %s RETURNING id", (product_id,))
        deleted = cur.fetchone()
        conn.commit()
        if not deleted:
            return {"status": "error", "message": "Product not found"}
        return {"status": "ok", "message": "Product deleted"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()
