from routes.user_routes import uuid
from werkzeug.utils import secure_filename
import os
UPLOAD_FOLDER = os.path.join("static", "uploads")
def save_image(file):
    # Secure original filename
    original = secure_filename(file.filename)

    # Get file extension
    ext = original.rsplit(".", 1)[1].lower()

    # Generate unique filename
    new_filename = f"{uuid.uuid4()}.{ext}"

    # Save file
    file_path = os.path.join(UPLOAD_FOLDER, new_filename)
    file.save(file_path)
    file.stream.close()

    return new_filename


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )