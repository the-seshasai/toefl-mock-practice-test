from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_connection, _record) -> None:
    cur = dbapi_connection.cursor()
    cur.execute("PRAGMA journal_mode=WAL")  # readers don't block the writer: tasks generate in parallel threads
    cur.execute("PRAGMA busy_timeout=15000")
    cur.close()

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# Lightweight forward migration for the local dev database: (table, column, DDL type)
_NEW_COLUMNS = [("responses", "meta", "JSON"), ("responses", "stage", "VARCHAR(10) DEFAULT 'main'"),
                ("section_attempts", "gen", "JSON")]


def _add_missing_columns() -> None:
    with engine.begin() as conn:
        for table, column, ddl in _NEW_COLUMNS:
            existing = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})")}
            if column not in existing:
                conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def init_db() -> None:
    from app import models  # noqa: F401  (register tables)

    Base.metadata.create_all(engine)
    _add_missing_columns()
    from app.generators.seed_bank import ensure_seeded

    with SessionLocal() as db:
        ensure_seeded(db)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
