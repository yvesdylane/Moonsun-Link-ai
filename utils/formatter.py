def format_listings(listings: list) -> str:
    if not listings:
        return "No listings found."

    lines = []
    for i, l in enumerate(listings):
        quantity = l[3]
        price = l[4]
        town = l[5] or "location not set"
        region = l[6]
        expires_at = l[9].strftime("%d %b %Y")

        lines.append(
            f"{i+1}) {quantity}kg at {price} XAF/kg\n"
            f"   📍 {town}, {region}\n"
            f"   ⏳ Expires: {expires_at}"
        )

    return "\n\n".join(lines)

def get_listing_images(listings: list) -> list[str]:
    """Returns list of image URLs from listings that have one."""
    return [l[8] for l in listings if l[8]]