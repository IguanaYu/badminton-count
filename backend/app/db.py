import math
import re
import sqlite3
from contextlib import closing

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from .config import settings

is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
sqlite_runtime_version = None

if is_sqlite:
    try:
        with closing(sqlite3.connect(":memory:")) as conn:
            version_str = conn.execute("select sqlite_version()").fetchone()[0]
        sqlite_runtime_version = tuple(int(part) for part in version_str.split("."))
    except sqlite3.Error:
        sqlite_runtime_version = sqlite3.sqlite_version_info

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    future=True,
)

if is_sqlite:
    def _setup_sqlite_functions(dbapi_connection, connection_record):
        def regexp(pattern: str, value: str | None) -> bool | None:
            if value is None:
                return None
            return re.search(pattern, value) is not None

        dbapi_connection.create_function("regexp", 2, regexp)
        dbapi_connection.create_function("floor", 1, math.floor)

    for fn in list(engine.pool.dispatch.connect):
        if fn.__name__ == "on_connect":
            event.remove(engine.pool, "connect", fn)

    event.listen(engine.pool, "connect", _setup_sqlite_functions)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True))

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
