from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker


def create_db_engine(database_url: str) -> Engine:
    options: dict = {}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        database_file = make_url(database_url).database
        if database_file and database_file != ":memory:":
            Path(database_file).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url, **options)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
