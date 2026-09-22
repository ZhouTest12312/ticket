from tests.conftest import auth_header


def _payload(**overrides):
    data = {
        "name": "星河教育",
        "contactName": "王敏",
        "phone": "13800001111",
        "email": "wang@example.com",
        "industry": "教育培训",
        "status": 1,
    }
    data.update(overrides)
    return data


def test_customer_forbidden_without_permission(client):
    headers = auth_header(client, "customer01")
    res = client.get("/api/customers", headers=headers)
    body = res.json()
    assert body["code"] == 403


def test_create_search_and_update_customer(client):
    headers = auth_header(client, "admin")
    created = client.post("/api/customers", headers=headers, json=_payload())
    assert created.json()["code"] == 200
    customer_id = created.json()["data"]["id"]

    stopped = client.post(
        "/api/customers",
        headers=headers,
        json=_payload(
            name="北城科技",
            contactName="李强",
            phone="13900002222",
            email="li@example.com",
            industry="互联网",
            status=0,
        ),
    )
    assert stopped.json()["code"] == 200

    by_name = client.get(
        "/api/customers", headers=headers, params={"name": "星河", "contact": "王敏", "page": 1, "pageSize": 10}
    )
    records = by_name.json()["data"]["records"]
    assert len(records) == 1
    assert records[0]["contactName"] == "王敏"

    by_contact = client.get(
        "/api/customers", headers=headers, params={"contact": "李强"}
    )
    assert by_contact.json()["data"]["total"] == 1

    by_status = client.get("/api/customers", headers=headers, params={"status": 0})
    assert by_status.json()["data"]["total"] == 1
    assert by_status.json()["data"]["records"][0]["name"] == "北城科技"

    updated = client.put(
        f"/api/customers/{customer_id}",
        headers=headers,
        json=_payload(contactName="王小敏", status=0),
    )
    assert updated.json()["code"] == 200
    detail = client.get(f"/api/customers/{customer_id}", headers=headers).json()
    assert detail["data"]["contactName"] == "王小敏"
    assert detail["data"]["status"] == 0


def test_customer_validation_and_ticket_history(client):
    headers = auth_header(client, "admin")
    bad = client.post(
        "/api/customers",
        headers=headers,
        json=_payload(email="not-an-email"),
    )
    assert bad.json()["code"] == 400

    created = client.post("/api/customers", headers=headers, json=_payload(name="历史客户"))
    customer_id = created.json()["data"]["id"]
    tickets = client.get(f"/api/customers/{customer_id}/tickets", headers=headers)
    body = tickets.json()
    assert body["code"] == 200
    assert body["data"]["total"] == 0
    assert body["data"]["records"] == []
