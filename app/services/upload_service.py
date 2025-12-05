from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import UPLOADS_DIR


def save_upload(file: UploadFile) -> str:
    suffix = Path(file.filename).suffix
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}{suffix}"
    destination = UPLOADS_DIR / unique_name
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb") as buffer:
        buffer.write(file.file.read())

    return f"/uploads/{unique_name}"
