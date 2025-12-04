import time
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile

from app.config import UPLOADS_DIR


def save_upload(file: UploadFile) -> Tuple[str, Path]:
    suffix = Path(file.filename).suffix
    unique_name = f"{int(time.time())}-{uuid.uuid4().hex}{suffix}"
    destination = UPLOADS_DIR / unique_name

    with destination.open("wb") as buffer:
        content = file.file.read()
        buffer.write(content)

    return unique_name, destination
