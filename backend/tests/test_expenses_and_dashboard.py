from datetime import date


def test_dashboard_is_admin_only(client, staff_token):
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.get("/dashboard/overview", headers=staff_headers)
    assert resp.status_code == 403


def test_dashboard_overview_math(client, admin_token, staff_token, branch, stock_item):
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    client.post(
        "/sales",
        json={"item_id": stock_item.id, "quantity_sold": 10},
        headers=staff_headers,
    )

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/dashboard/overview", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    branch_summary = next(b for b in body["branches"] if b["branch_id"] == branch.id)
    assert branch_summary["total_sales"] == 10 * stock_item.price
    assert body["total_sales"] == 10 * stock_item.price


def test_dashboard_monthly(client, admin_token, staff_token, stock_item):
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    client.post(
        "/sales",
        json={"item_id": stock_item.id, "quantity_sold": 1},
        headers=staff_headers,
    )

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    today = date.today()
    resp = client.get(
        "/dashboard/monthly", params={"year": today.year, "month": today.month}, headers=admin_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_sales"] == stock_item.price

    todays_point = next(d for d in body["daily"] if d["date"] == today.isoformat())
    assert todays_point["total_sales"] == stock_item.price
    other_point = next(d for d in body["daily"] if d["date"] != today.isoformat())
    assert other_point["total_sales"] == 0
