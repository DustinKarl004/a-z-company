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


def test_delivery_role_staff_created_without_branch(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/staff",
        json={
            "name": "Del Ivery",
            "email": "delivery@example.com",
            "password": "staffpass123",
            "roles": ["delivery"],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["roles"] == ["delivery"]
    assert body["branch_id"] is None


def test_staff_role_still_requires_branch(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/staff",
        json={
            "name": "No Branch",
            "email": "nobranch@example.com",
            "password": "staffpass123",
            "roles": ["staff"],
        },
        headers=headers,
    )
    assert resp.status_code == 400


def test_switching_delivery_staff_to_staff_role_requires_branch(client, admin_token, branch):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/staff",
        json={
            "name": "Del Ivery",
            "email": "delivery2@example.com",
            "password": "staffpass123",
            "roles": ["delivery"],
        },
        headers=headers,
    )
    staff_id = resp.json()["id"]

    resp = client.patch(f"/staff/{staff_id}", json={"roles": ["staff"]}, headers=headers)
    assert resp.status_code == 400

    resp = client.patch(
        f"/staff/{staff_id}", json={"roles": ["staff"], "branch_id": branch.id}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["branch_id"] == branch.id


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
    # branch listing is intentionally staff-readable so all-branch delivery staff can pick a branch
    assert client.get("/branches", headers=staff_headers).status_code == 200
    assert client.post("/branches", json={"name": "New"}, headers=staff_headers).status_code == 403
