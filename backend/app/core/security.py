"""Small security helpers."""
import os
import re
import unicodedata


def sanitize_filename(name: str | None, max_length: int = 100) -> str:
    """Make a user-supplied file name safe to store and display.

    The name is only used for display. Files are saved on disk under a random
    name, so this is a second layer of protection, not the only one.
    """
    if not name:
        return "document"

    name = name.replace("\\", "/").split("/")[-1]          # drop any folder path
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)             # control characters
    name = re.sub(r'[<>:"|?*]', "_", name)                  # awkward characters
    name = name.strip(" .")
    if not name:
        return "document"

    if len(name) > max_length:
        stem, extension = os.path.splitext(name)
        name = stem[: max_length - len(extension)] + extension
    return name
