from tests.conftest import auth_header


def test_dict_item_controls_ticket_options(client):
    headers = auth_header(client, "admin")
    types = client.get("/api/dict-types", headers=headers).json()
    assert types["code"] == 200
    codes = {row["code"] for row in types["data"]}
    assert codes == {"product", "service"}

    created = client.post(
        "/api/dict-items",
        headers=headers,
        json={"typeCode": "product", "name": "校园平台", "sort": 1, "status": 1},
    )
    assert created.json()["code"] == 200
    item_id = created.json()["data"]["id"]

    options = client.get("/api/tickets/options", headers=headers).json()["data"]
    assert "校园平台" in [row["name"] for row in options["products"]]

    disabled = client.put(
        f"/api/dict-items/{item_id}",
        headers=headers,
        json={"name": "校园平台", "sort": 1, "status": 0},
    )
    assert disabled.json()["code"] == 200
    options = client.get("/api/tickets/options", headers=headers).json()["data"]
    assert "校园平台" not in [row["name"] for row in options["products"]]

    denied = client.get("/api/dict-types", headers=auth_header(client, "customer01"))
    assert denied.json()["code"] == 403


def test_create_dict_type(client):
    headers = auth_header(client, "admin")
    created = client.post("/api/dict-types", headers=headers, json={"name": "问题来源"})
    assert created.json()["code"] == 200
    names = {row["name"] for row in client.get("/api/dict-types", headers=headers).json()["data"]}
    assert "问题来源" in names
    duplicated = client.post("/api/dict-types", headers=headers, json={"name": "问题来源"})
    assert duplicated.json()["code"] == 400
    type_id = created.json()["data"]["id"]
    updated = client.put(
        f"/api/dict-types/{type_id}", headers=headers, json={"name": "问题渠道"}
    )
    assert updated.json()["code"] == 200
    removed = client.delete(f"/api/dict-types/{type_id}", headers=headers)
    assert removed.json()["code"] == 200
