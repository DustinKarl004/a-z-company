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


def test_totp_setup_enable_and_login_requires_code(client, admin_token):
    import pyotp

    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.get("/settings/totp", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"enabled": False}

    resp = client.post("/settings/totp/setup", headers=headers)
    assert resp.status_code == 200
    secret = resp.json()["secret"]
    assert resp.json()["otpauth_uri"].startswith("otpauth://")

    code = pyotp.TOTP(secret).now()
    resp = client.post("/settings/totp/enable", json={"secret": secret, "code": code}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is True
    assert len(body["backup_codes"]) == 10

    resp = client.post("/auth/login", json={"email": "admin@example.com", "password": "adminpass123"})
    assert resp.status_code == 401

    resp = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123", "totp_code": pyotp.TOTP(secret).now()},
    )
    assert resp.status_code == 200


def test_totp_enable_with_wrong_code_fails(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.post("/settings/totp/setup", headers=headers)
    secret = resp.json()["secret"]

    resp = client.post("/settings/totp/enable", json={"secret": secret, "code": "000000"}, headers=headers)
    assert resp.status_code == 400

    resp = client.get("/settings/totp", headers=headers)
    assert resp.json() == {"enabled": False}


def test_totp_disable_requires_correct_password(client, admin_token):
    import pyotp

    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.post("/settings/totp/setup", headers=headers)
    secret = resp.json()["secret"]
    client.post("/settings/totp/enable", json={"secret": secret, "code": pyotp.TOTP(secret).now()}, headers=headers)

    resp = client.post("/settings/totp/disable", json={"password": "wrongpass"}, headers=headers)
    assert resp.status_code == 403

    resp = client.post("/settings/totp/disable", json={"password": "adminpass123"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"enabled": False}


def test_login_with_backup_code_then_reuse_fails(client, admin_token):
    import pyotp

    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.post("/settings/totp/setup", headers=headers)
    secret = resp.json()["secret"]
    resp = client.post("/settings/totp/enable", json={"secret": secret, "code": pyotp.TOTP(secret).now()}, headers=headers)
    backup_code = resp.json()["backup_codes"][0]

    resp = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123", "totp_code": backup_code},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123", "totp_code": backup_code},
    )
    assert resp.status_code == 401


def test_disabling_totp_clears_backup_codes(client, admin_token, db_session):
    import pyotp

    from app.crud.users import get_user_by_email

    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.post("/settings/totp/setup", headers=headers)
    secret = resp.json()["secret"]
    client.post("/settings/totp/enable", json={"secret": secret, "code": pyotp.TOTP(secret).now()}, headers=headers)

    client.post("/settings/totp/disable", json={"password": "adminpass123"}, headers=headers)

    user = get_user_by_email(db_session, "admin@example.com")
    assert user.backup_codes is None
