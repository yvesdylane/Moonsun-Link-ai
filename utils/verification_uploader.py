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

def upload_verification_file(file_path: str, user_id: str, file_type: str) -> dict:
    """
    Upload verification files (selfie or ID) to Cloudinary.

    Args:
        file_path: Path to the file to upload
        user_id: User ID for folder organization
        file_type: Either 'selfie' or 'id'

    Returns:
        dict with status, url, and message
    """
    # Check file size (max 2MB)
    file_size = os.path.getsize(file_path)
    max_size = 2 * 1024 * 1024  # 2MB in bytes

    if file_size > max_size:
        return {
            "status": "error",
            "message": f"File too large ({file_size / 1024 / 1024:.1f}MB). Maximum size is 2MB."
        }

    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    _, ext = os.path.splitext(file_path.lower())

    if ext not in allowed_extensions:
        return {
            "status": "error",
            "message": f"Invalid file format. Accepted formats: JPEG, PNG, PDF"
        }

    try:
        # Compress image (skip PDFs)
        if ext != '.pdf':
            compressed = compress_image(file_path)
            tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            tmp.write(compressed)
            tmp.close()
            upload_path = tmp.name
        else:
            upload_path = file_path

        # Upload to Cloudinary in user-specific folder
        folder = f"moonso/users/{user_id}"
        public_id = f"{file_type}_{user_id}"

        result = cloudinary.uploader.upload(
            upload_path,
            folder=folder,
            public_id=public_id,
            resource_type="auto",  # Handles images and PDFs
            overwrite=True
        )

        # Clean up temp file if created
        if ext != '.pdf':
            os.unlink(upload_path)

        return {
            "status": "ok",
            "url": result["secure_url"],
            "message": f"{file_type.capitalize()} uploaded successfully"
        }
    except Exception as e:
        print(f"CLOUDINARY VERIFICATION ERROR: {e}")
        return {
            "status": "error",
            "message": "Failed to upload file. Please try again."
        }
