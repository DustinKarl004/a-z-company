def test_admin_can_create_list_update_staff(client, admin_token, branch):
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.post(
        "/staff",
        json={
            "name": "Jane Staff",
            "email": "jane@example.com",
            "password": "staffpass123",
            "branch_id": branch.id,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    staff = resp.json()
    assert staff["role"] == "staff"
    assert staff["branch_id"] == branch.id

    resp = client.get("/staff", headers=headers)
    assert resp.status_code == 200
    assert any(s["email"] == "jane@example.com" for s in resp.json())

    resp = client.patch(f"/staff/{staff['id']}", json={"is_active": False}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_create_staff_requires_valid_branch(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/staff",
        json={
            "name": "Jane Staff",
            "email": "jane2@example.com",
            "password": "staffpass123",
            "branch_id": "doesnotexist",
        },
        headers=headers,
    )
    assert resp.status_code == 400


def test_staff_cannot_access_admin_routes(client, admin_token, branch):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/staff",
        json={
            "name": "Jane Staff",
            "email": "jane3@example.com",
            "password": "staffpass123",
            "branch_id": branch.id,
        },
        headers=headers,
    )
    assert resp.status_code == 201

    login_resp = client.post(
        "/auth/login", json={"email": "jane3@example.com", "password": "staffpass123"}
    )
    assert login_resp.status_code == 200
    staff_token = login_resp.json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    assert client.get("/staff", headers=staff_headers).status_code == 403
    assert client.get("/branches", headers=staff_headers).status_code == 403
