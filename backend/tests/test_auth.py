def test_login_success(client, admin_token):
    assert admin_token


def test_login_wrong_password(client, db_session):
    from app.crud.users import create_user

    create_user(
        db_session,
        name="Admin",
        email="admin2@example.com",
        password="correctpass1",
        role="admin",
        branch_id=None,
    )
    resp = client.post("/auth/login", json={"email": "admin2@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email(client, db_session):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever1"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client, db_session):
    resp = client.get("/branches")
    assert resp.status_code == 401
