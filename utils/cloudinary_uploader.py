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

