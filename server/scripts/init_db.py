"""Create tables and seed. Supports MySQL or SQLite (USE_SQLITE=true)."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models import Customer, Permission, Role, Ticket, User  # noqa: F401,E402
from scripts.seed_data import seed_all  # noqa: E402


def ensure_database() -> None:
    if settings.use_sqlite:
        return
    url = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/?charset=utf8mb4"
    )
    engine = create_engine(url, future=True)
    with engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_database}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
        conn.commit()
    engine.dispose()


def main() -> None:
    ensure_database()
    connect_args = {"check_same_thread": False} if settings.use_sqlite else {}
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=not settings.use_sqlite,
        connect_args=connect_args,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        seed_all(db)
        mode = "sqlite" if settings.use_sqlite else f"mysql:{settings.mysql_database}"
        print(f"OK: database ready ({mode}) with seed data")
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    main()
