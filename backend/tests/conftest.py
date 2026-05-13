import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# In-memory SQLite with StaticPool so all connections share the same DB
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def registered_user(client):
    """Register a user and return their token."""
    client.post("/auth/register", json={"email": "test@example.com", "password": "testpass123"})
    res = client.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    token = res.json()["access_token"]
    return {"token": token, "email": "test@example.com"}


@pytest.fixture
def auth_headers(registered_user):
    return {"Authorization": f"Bearer {registered_user['token']}"}
