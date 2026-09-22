from app.core.security import md5_hex


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 200
    assert body["data"]["status"] == "up"


def test_login_ok(client):
    res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": md5_hex("Admin@123")},
    )
    body = res.json()
    assert body["code"] == 200
    assert body["data"]["token"]


def test_login_wrong_password(client):
    res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": md5_hex("bad")},
    )
    body = res.json()
    assert body["code"] in (400, 401)
    assert body["msg"]


def test_me_unauthorized(client):
    res = client.get("/api/auth/me")
    body = res.json()
    assert body["code"] == 401
    assert body["msg"] == "请先登录"


def test_me_ok(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": md5_hex("Admin@123")},
    )
    token = login.json()["data"]["token"]
    res = client.get("/api/auth/me", headers={"Authorization": token})
    body = res.json()
    assert body["code"] == 200
    assert "role:write" in body["data"]["permissions"]
    assert body["data"]["menus"]
    assert body["data"]["name"]
    assert body["data"]["jobNumber"] == "admin"


def test_change_password(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": md5_hex("Admin@123")},
    )
    token = login.json()["data"]["token"]
    res = client.put(
        "/api/auth/password",
        headers={"Authorization": token},
        json={
            "oldPassword": md5_hex("Admin@123"),
            "newPassword": md5_hex("Admin@456"),
        },
    )
    assert res.json()["code"] == 200
    again = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": md5_hex("Admin@456")},
    )
    assert again.json()["code"] == 200
