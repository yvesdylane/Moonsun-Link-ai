from db.connect import conn

def get_listings(page=1, limit=10):
    cur = conn.cursor()
    offset = (page - 1) * limit
    query = """SELECT * FROM listings LIMIT %s OFFSET %s"""
    cur.execute(query, (limit, offset))
    listings = cur.fetchall()
    for listing in listings:
        print(listing)
    cur.close()
    return listings

get_listings(1, 5)