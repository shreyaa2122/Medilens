import uuid

from sqlalchemy.orm import Session

from app.db.models import User

# Fixed id of the single built-in user (until real login exists).
DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def ensure_default_user(db: Session) -> None:
    if db.get(User, DEFAULT_USER_ID) is None:
        db.add(User(id=DEFAULT_USER_ID))
        db.commit()
