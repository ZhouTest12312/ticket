from app.core.security import md5_hex
from tests.conftest import auth_header


def test_create_user_gets_role_permissions_and_group(client):
    headers = auth_header(client, "admin")
    roles = client.get("/api/roles", headers=headers, params={"page": 1, "pageSize": 50}).json()["data"]["records"]
    cs = next(item for item in roles if item["code"] == "cs")
    admin_role = next(item for item in roles if item["code"] == "admin")
    created = client.post(
        "/api/users",
        headers=headers,
        json={"username": "002", "displayName": "客服002", "roleIds": [cs["id"]]},
    )
    assert created.json()["code"] == 200
    login = client.post(
        "/api/auth/login",
        json={"username": "002", "password": md5_hex("admin123")},
    )
    assert login.json()["code"] == 200
    token = login.json()["data"]["token"]
    me = client.get("/api/auth/me", headers={"Authorization": token}).json()["data"]
    assert "ticket:create" in me["permissions"]
    assert "ticket:view_all" not in me["permissions"]
    assert "ticket:view_own" in me["permissions"]
    assert "user:write" not in me["permissions"]
    users = client.get("/api/users", headers=headers, params={"keyword": "002"}).json()["data"]["records"]
    row = next(item for item in users if item["username"] == "002")
    assert row["groups"][0]["name"] == "客服组"
    second_admin = client.post(
        "/api/users",
        headers=headers,
        json={"username": "admin2", "displayName": "另一个管理员", "roleIds": [admin_role["id"]]},
    )
    assert second_admin.json()["code"] == 400
    assert "管理员只能有一个" in second_admin.json()["msg"]
