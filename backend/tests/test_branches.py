def test_admin_can_create_and_list_branches(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = client.post("/branches", json={"name": "Quezon City"}, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Quezon City"
    assert len(body["id"]) == 12

    resp = client.get("/branches", headers=headers)
    assert resp.status_code == 200
    names = [b["name"] for b in resp.json()]
    assert "Quezon City" in names
