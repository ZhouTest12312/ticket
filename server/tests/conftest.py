import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Customer, Permission, Role, Ticket, User  # noqa: F401
from app.core.security import md5_hex
from scripts.seed_data import seed_all


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    db = TestingSessionLocal()
    seed_all(db)
    db.close()

    def _get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def auth_header(client: TestClient, username: str = "admin") -> dict:
    res = client.post(
        "/api/auth/login",
        json={"username": username, "password": md5_hex("Admin@123")},
    )
    token = res.json()["data"]["token"]
    return {"Authorization": token}
