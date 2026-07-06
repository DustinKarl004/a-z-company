from datetime import date


def test_expenses_are_admin_only(client, admin_token, staff_token, branch):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    resp = client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Ice", "amount": 100},
        headers=admin_headers,
    )
    assert resp.status_code == 201

    resp = client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Ice", "amount": 100},
        headers=staff_headers,
    )
    assert resp.status_code == 403

    resp = client.get("/expenses", headers=staff_headers)
    assert resp.status_code == 403


def test_dashboard_is_admin_only(client, staff_token):
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.get("/dashboard/overview", headers=staff_headers)
    assert resp.status_code == 403


def test_dashboard_overview_math(client, admin_token, staff_token, branch, stock_item):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    client.post(
        "/sales",
        json={"item_id": stock_item.id, "quantity_sold": 10, "amount": 500},
        headers=staff_headers,
    )
    client.post(
        "/expenses",
        json={"branch_id": branch.id, "description": "Supplies", "amount": 120},
        headers=admin_headers,
    )

    resp = client.get("/dashboard/overview", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    branch_summary = next(b for b in body["branches"] if b["branch_id"] == branch.id)
    assert branch_summary["total_sales"] == 500
    assert branch_summary["total_expenses"] == 120
    assert branch_summary["profit"] == 380
    assert body["total_profit"] == 380


def test_dashboard_monthly(client, admin_token, staff_token, stock_item):
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    client.post(
        "/sales",
        json={"item_id": stock_item.id, "quantity_sold": 1, "amount": 50},
        headers=staff_headers,
    )

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    today = date.today()
    resp = client.get(
        "/dashboard/monthly", params={"year": today.year, "month": today.month}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["total_sales"] == 50
