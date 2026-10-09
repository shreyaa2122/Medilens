"""Saves and deletes uploaded files in one controlled folder.

Files are stored under a random name (never the user's file name), so a
malicious file name can never choose where a file is written.
"""
import os
import uuid
from pathlib import Path


class StorageService:
    def __init__(self, upload_dir: str):
        self.root = Path(upload_dir).resolve()

    def save(self, content: bytes, extension: str) -> str:
        """Write the file and return the random stored name."""
        self.root.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid.uuid4().hex}.{extension}"
        path = self._path_for(stored_name)
        with open(path, "xb") as file:
            file.write(content)
        try:
            os.chmod(path, 0o600)  # owner-only access (ignored on Windows)
        except OSError:
            pass
        return stored_name

    def delete(self, stored_name: str) -> None:
        self._path_for(stored_name).unlink(missing_ok=True)

    def _path_for(self, stored_name: str) -> Path:
        path = (self.root / stored_name).resolve()
        if path.parent != self.root:
            raise ValueError("Invalid stored file name.")
        return path
