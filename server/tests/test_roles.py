from tests.conftest import auth_header


def test_create_role_forbidden_for_customer(client):
    headers = auth_header(client, "customer01")
    res = client.post(
        "/api/roles",
        headers=headers,
        json={"code": "x", "name": "x", "permissionIds": []},
    )
    body = res.json()
    assert body["code"] == 403
    assert "当前没有权限执行此操作" in body["msg"]


def test_cannot_delete_system_role(client):
    headers = auth_header(client, "admin")
    roles = client.get("/api/roles", headers=headers, params={"page": 1, "pageSize": 50})
    admin_role = next(r for r in roles.json()["data"]["records"] if r["code"] == "admin")
    res = client.delete(f"/api/roles/{admin_role['id']}", headers=headers)
    body = res.json()
    assert body["code"] == 400
    assert "系统角色" in body["msg"]


def test_cannot_delete_role_assigned_to_users(client):
    headers = auth_header(client, "admin")
    created = client.post(
        "/api/roles",
        headers=headers,
        json={"code": "assigned_role", "name": "已分配角色", "permissionIds": []},
    )
    assert created.json()["code"] == 200
    role_id = created.json()["data"]["id"]
    users = client.get("/api/users", headers=headers, params={"page": 1, "pageSize": 10})
    user_id = users.json()["data"]["records"][0]["id"]
    old_roles = [r["id"] for r in users.json()["data"]["records"][0]["roles"]]
    assign = client.put(
        f"/api/users/{user_id}/roles",
        headers=headers,
        json={"roleIds": old_roles + [role_id]},
    )
    assert assign.json()["code"] == 200
    res = client.delete(f"/api/roles/{role_id}", headers=headers)
    body = res.json()
    assert body["code"] == 400
    assert "已分配" in body["msg"]
    assert "用户管理" in body["msg"]


def test_create_and_get_role(client):
    headers = auth_header(client, "admin")
    perms = client.get("/api/permissions", headers=headers).json()["data"]
    pid = perms[0]["items"][0]["id"]
    created = client.post(
        "/api/roles",
        headers=headers,
        json={
            "code": "demo",
            "name": "演示",
            "description": "d",
            "permissionIds": [pid],
        },
    )
    assert created.json()["code"] == 200
    role_id = created.json()["data"]["id"]
    detail = client.get(f"/api/roles/{role_id}", headers=headers).json()
    assert detail["code"] == 200
    assert detail["data"]["permissionIds"] == [pid]
