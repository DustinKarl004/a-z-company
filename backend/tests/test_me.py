def test_staff_can_view_and_update_own_branch(client, staff_token, branch2):
    headers = {"Authorization": f"Bearer {staff_token}"}

    resp = client.get("/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["roles"] == ["staff"]

    resp = client.patch("/me/branch", json={"branch_id": branch2.id}, headers=headers)
    assert resp.status_code == 200
    new_token = resp.json()["access_token"]

    resp = client.get("/me", headers={"Authorization": f"Bearer {new_token}"})
    assert resp.status_code == 200
    assert resp.json()["branch_id"] == branch2.id
    assert resp.json()["branch_name"] == "Second Branch"


def test_staff_branch_update_rejects_invalid_branch(client, staff_token):
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.patch("/me/branch", json={"branch_id": "doesnotexist"}, headers=headers)
    assert resp.status_code == 400


def test_delivery_role_cannot_update_branch(client, delivery_token, branch):
    headers = {"Authorization": f"Bearer {delivery_token}"}
    resp = client.patch("/me/branch", json={"branch_id": branch.id}, headers=headers)
    assert resp.status_code == 400


def test_staff_can_change_own_password(client, staff_token):
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.post(
        "/me/password",
        json={"current_password": "staffpass123", "new_password": "newpass456"},
        headers=headers,
    )
    assert resp.status_code == 204

    resp = client.post("/auth/login", json={"email": "staff@example.com", "password": "newpass456"})
    assert resp.status_code == 200


def test_password_change_requires_correct_current_password(client, staff_token):
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.post(
        "/me/password",
        json={"current_password": "wrongpass", "new_password": "newpass456"},
        headers=headers,
    )
    assert resp.status_code == 401


def test_admin_cannot_access_me_routes(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/me", headers=headers)
    assert resp.status_code == 403
