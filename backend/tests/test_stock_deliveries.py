from datetime import date, timedelta


def test_staff_can_create_and_list_own_branch_delivery(client, staff_token, branch, stock_item):
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.post(
        "/stock-deliveries",
        json={"item_id": stock_item.id, "quantity_delivered": 50, "is_short": False},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["branch_id"] == branch.id
    assert body["date"] == date.today().isoformat()

    resp = client.get("/stock-deliveries", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_staff_cannot_create_for_another_branch(client, staff_token, branch2, stock_item):
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.post(
        "/stock-deliveries",
        json={
            "branch_id": branch2.id,
            "item_id": stock_item.id,
            "quantity_delivered": 10,
            "is_short": False,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["branch_id"] != branch2.id


def test_staff_cannot_backdate_delivery(client, staff_token, stock_item):
    headers = {"Authorization": f"Bearer {staff_token}"}
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    resp = client.post(
        "/stock-deliveries",
        json={
            "item_id": stock_item.id,
            "date": yesterday,
            "quantity_delivered": 10,
            "is_short": False,
        },
        headers=headers,
    )
    assert resp.status_code == 400


def test_staff_cannot_edit_yesterdays_delivery(client, admin_token, staff_token, branch, stock_item):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    resp = client.post(
        "/stock-deliveries",
        json={
            "branch_id": branch.id,
            "item_id": stock_item.id,
            "date": yesterday,
            "quantity_delivered": 10,
            "is_short": False,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    delivery_id = resp.json()["id"]

    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.patch(
        f"/stock-deliveries/{delivery_id}", json={"quantity_delivered": 99}, headers=staff_headers
    )
    assert resp.status_code == 403


def test_staff_can_edit_todays_delivery(client, staff_token, stock_item):
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = client.post(
        "/stock-deliveries",
        json={"item_id": stock_item.id, "quantity_delivered": 10, "is_short": False},
        headers=headers,
    )
    delivery_id = resp.json()["id"]

    resp = client.patch(
        f"/stock-deliveries/{delivery_id}", json={"is_short": True}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["is_short"] is True


def test_staff_cannot_see_another_branchs_deliveries(
    client, staff_token, staff_token2, branch2, stock_item
):
    headers2 = {"Authorization": f"Bearer {staff_token2}"}
    client.post(
        "/stock-deliveries",
        json={"item_id": stock_item.id, "quantity_delivered": 5, "is_short": False},
        headers=headers2,
    )

    headers1 = {"Authorization": f"Bearer {staff_token}"}
    resp = client.get("/stock-deliveries", headers=headers1)
    assert resp.status_code == 200
    assert resp.json() == []


def test_admin_can_filter_by_branch_and_date(client, admin_token, branch, stock_item):
    headers = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        "/stock-deliveries",
        json={"branch_id": branch.id, "item_id": stock_item.id, "quantity_delivered": 5, "is_short": False},
        headers=headers,
    )
    resp = client.get(
        "/stock-deliveries",
        params={"branch_id": branch.id, "date": date.today().isoformat()},
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
