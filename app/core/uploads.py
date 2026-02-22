import os
import uuid
from pathlib import Path

from fastapi import UploadFile

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
UPLOAD_DIR = Path("app/static/uploads")


def save_image_upload(upload: UploadFile, prefix: str = "foto") -> str:
    if not upload or not upload.filename:
        return None

    ext = Path(upload.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise ValueError("Formato de imagem inválido. Use JPG, PNG, WEBP ou GIF")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
    full_path = UPLOAD_DIR / filename

    content = upload.file.read()
    if len(content) == 0:
        raise ValueError("Arquivo de imagem vazio")

    with open(full_path, "wb") as f:
        f.write(content)

    return f"/static/uploads/{filename}"


def remove_uploaded_file(static_path: str):
    if not static_path or not static_path.startswith("/static/uploads/"):
        return

    filename = os.path.basename(static_path)
    full_path = UPLOAD_DIR / filename
    if full_path.exists():
        full_path.unlink()

