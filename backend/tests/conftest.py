import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.crud.branches import create_branch
from app.crud.users import create_user
from app.main import app
from app.models import Base


@pytest.fixture()
def db_session():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.clear()
        engine.dispose()
        os.remove(path)


@pytest.fixture()
def client(db_session):
    return TestClient(app)


@pytest.fixture()
def admin_token(client, db_session):
    create_user(
        db_session,
        name="Admin",
        email="admin@example.com",
        password="adminpass123",
        role="admin",
        branch_id=None,
    )
    resp = client.post("/auth/login", json={"email": "admin@example.com", "password": "adminpass123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture()
def branch(db_session):
    return create_branch(db_session, name="Main Branch")
