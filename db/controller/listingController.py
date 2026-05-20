from db.connect import conn

def get_listing():
    cur = conn.cursor()
    cur.execute("select * from listings")
    listings = cur.fetchall()
    for listing in listings:
        print(listing)
    cur.close()

get_listing()