import cloudinary
import cloudinary.uploader
import os
import tempfile
from dotenv import load_dotenv
from utils.image_compressor import compress_image

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image(file_path: str) -> str | None:
    try:
        compressed = compress_image(file_path)
        suffix = os.path.splitext(file_path)[1] or ".jpg"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(compressed)
        tmp.close()
        result = cloudinary.uploader.upload(tmp.name, folder="moonso/listings")
        os.unlink(tmp.name)
        return result["secure_url"]
    except Exception as e:
        print(f"CLOUDINARY ERROR: {e}")
        return None


def get_cloudinary_url(public_id: str, resource_type: str = "image") -> str | None:
    """
    Get the secure URL for a Cloudinary resource by its public_id.

    Args:
        public_id: The full public ID (e.g. "moonso/users/{uuid}/selfie_{uuid}")
        resource_type: 'image', 'raw', 'video', or 'auto'

    Returns:
        The secure URL string, or None if not found.
    """
    try:
        result = cloudinary.api.resource(public_id, resource_type=resource_type)
        return result.get("secure_url")
    except Exception as e:
        print(f"CLOUDINARY RESOURCE LOOKUP ERROR ({public_id}): {e}")
        return None