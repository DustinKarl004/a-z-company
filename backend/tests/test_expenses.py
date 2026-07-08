from datetime import date


def test_expenses_admin_only(client, staff_token):
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.get("/expenses", headers=staff_headers)
    assert resp.status_code == 403

    resp = client.post(
        "/expenses",
        json={"branch_id": "whatever", "description": "Ice", "amount": 100},
        headers=staff_headers,
    )
    assert resp.status_code == 403


def test_create_and_list_expense(client, admin_token, branch):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Ice", "amount": 150.0},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["branch_id"] == branch.id
    assert body["description"] == "Ice"
    assert body["amount"] == 150.0
    assert body["date"] == date.today().isoformat()

    resp = client.get("/expenses", params={"date": date.today().isoformat()}, headers=admin_headers)
    assert resp.status_code == 200
    listed = resp.json()
    assert len(listed) == 1
    assert listed[0]["id"] == body["id"]


def test_create_expense_requires_branch_id(client, admin_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/expenses",
        json={"description": "Ice", "amount": 150.0},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_list_expenses_filters_by_branch(client, admin_token, branch, branch2):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Ice", "amount": 100.0},
        headers=admin_headers,
    )
    client.post(
        "/expenses",
        json={"branch_id": branch2.id, "description": "Water", "amount": 50.0},
        headers=admin_headers,
    )

    resp = client.get("/expenses", params={"branch_id": branch.id}, headers=admin_headers)
    assert resp.status_code == 200
    listed = resp.json()
    assert len(listed) == 1
    assert listed[0]["description"] == "Ice"


def test_delete_expense(client, admin_token, branch):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Ice", "amount": 100.0},
        headers=admin_headers,
    )
    expense_id = resp.json()["id"]

    resp = client.request(
        "DELETE", f"/expenses/{expense_id}", json={"password": "adminpass123"}, headers=admin_headers
    )
    assert resp.status_code == 204

    resp = client.get("/expenses", headers=admin_headers)
    assert resp.json() == []

    resp = client.request(
        "DELETE", f"/expenses/{expense_id}", json={"password": "adminpass123"}, headers=admin_headers
    )
    assert resp.status_code == 404


def test_delete_month_data(client, admin_token, branch):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    may_expense = client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Ice", "amount": 100.0, "date": "2026-05-15"},
        headers=admin_headers,
    ).json()
    june_expense = client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Water", "amount": 50.0, "date": "2026-06-15"},
        headers=admin_headers,
    ).json()

    resp = client.request(
        "DELETE",
        "/expenses/month",
        params={"year": 2026, "month": 5},
        json={"password": "adminpass123"},
        headers=admin_headers,
    )
    assert resp.status_code == 204

    resp = client.get("/expenses", headers=admin_headers)
    remaining_ids = {e["id"] for e in resp.json()}
    assert may_expense["id"] not in remaining_ids
    assert june_expense["id"] in remaining_ids


def test_delete_month_data_keeps_last_day_stock_count(client, admin_token, branch, stock_item):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    mid_month_count = client.post(
        "/stock-counts",
        json={"branch_id": branch.id, "item_id": stock_item.id, "date": "2026-05-15", "quantity_remaining": 10},
        headers=admin_headers,
    ).json()
    last_day_count = client.post(
        "/stock-counts",
        json={"branch_id": branch.id, "item_id": stock_item.id, "date": "2026-05-31", "quantity_remaining": 5},
        headers=admin_headers,
    ).json()

    resp = client.request(
        "DELETE",
        "/expenses/month",
        params={"year": 2026, "month": 5},
        json={"password": "adminpass123"},
        headers=admin_headers,
    )
    assert resp.status_code == 204

    resp = client.get("/stock-counts", headers=admin_headers)
    remaining_ids = {c["id"] for c in resp.json()}
    assert mid_month_count["id"] not in remaining_ids
    assert last_day_count["id"] in remaining_ids


def test_delete_month_data_rejects_current_and_future_month(client, admin_token, branch):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    today = date.today()

    resp = client.request(
        "DELETE",
        "/expenses/month",
        params={"year": today.year, "month": today.month},
        json={"password": "adminpass123"},
        headers=admin_headers,
    )
    assert resp.status_code == 400

    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1
    resp = client.request(
        "DELETE",
        "/expenses/month",
        params={"year": next_year, "month": next_month},
        json={"password": "adminpass123"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_delete_month_data_requires_correct_password(client, admin_token, branch):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Ice", "amount": 100.0, "date": "2026-05-15"},
        headers=admin_headers,
    )

    resp = client.request(
        "DELETE",
        "/expenses/month",
        params={"year": 2026, "month": 5},
        json={"password": "wrongpass"},
        headers=admin_headers,
    )
    assert resp.status_code == 401

    resp = client.get("/expenses", headers=admin_headers)
    assert len(resp.json()) == 1


def test_delete_expense_requires_correct_password(client, admin_token, branch):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Ice", "amount": 100.0},
        headers=admin_headers,
    )
    expense_id = resp.json()["id"]

    resp = client.request(
        "DELETE", f"/expenses/{expense_id}", json={"password": "wrongpass"}, headers=admin_headers
    )
    assert resp.status_code == 401
