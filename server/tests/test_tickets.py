from app.core.security import md5_hex
from tests.conftest import auth_header


def _ids(client, headers):
    options = client.get("/api/tickets/options", headers=headers).json()["data"]
    if options.get("customers"):
        customer_id = options["customers"][0]["id"]
    else:
        roles = client.get("/api/roles", headers=headers, params={"page": 1, "pageSize": 50}).json()["data"]["records"]
        customer_role = next(item for item in roles if item["code"] == "customer")
        portal = client.post(
            "/api/users",
            headers=headers,
            json={"username": "portal_ask", "displayName": "门户客户", "roleIds": [customer_role["id"]]},
        )
        assert portal.json()["code"] == 200
        customer = client.post(
            "/api/customers",
            headers=headers,
            json={
                "name": "工单客户",
                "contactName": "赵六",
                "phone": "13700001111",
                "email": "zhao@example.com",
                "industry": "教育",
                "status": 1,
                "userId": portal.json()["data"]["id"],
            },
        ).json()["data"]
        customer_id = customer["id"]
        options = client.get("/api/tickets/options", headers=headers).json()["data"]
    for type_code, name in (("product", "工单系统"), ("service", "账号服务")):
        created_item = client.post(
            "/api/dict-items",
            headers=headers,
            json={"typeCode": type_code, "name": name, "sort": 1, "status": 1},
        )
        assert created_item.json()["code"] == 200
    return {
        "categoryId": options["categories"][0]["id"],
        "priorityId": options["priorities"][-1]["id"],
        "customerId": customer_id,
        "users": options["users"],
        "groups": options["groups"],
    }


def _group_id(meta, name):
    return next(item["id"] for item in meta["groups"] if item["name"] == name)


def _create(client, headers, meta, **extra):
    body = {
        "title": "无法登录",
        "description": "点击登录没有反应",
        "categoryId": meta["categoryId"],
        "priorityId": meta["priorityId"],
        "customerId": meta["customerId"],
        "product": "工单系统",
        "orderNo": "SO-1",
        "serviceName": "账号服务",
        "expectedFinishAt": "2026-09-22 18:00:00",
    }
    body.update(extra)
    return client.post("/api/tickets", headers=headers, json=body)


def test_create_assign_and_logs(client):
    headers = auth_header(client, "admin")
    meta = _ids(client, headers)
    created = _create(client, headers, meta)
    assert created.json()["code"] == 200
    ticket_id = created.json()["data"]["id"]
    assignee = next(u for u in meta["users"] if u["name"] == "技术01")
    assigned = client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=headers,
        json={"assigneeId": assignee["id"], "groupId": _group_id(meta, "技术组")},
    )
    assert assigned.json()["code"] == 200
    detail = client.get(f"/api/tickets/{ticket_id}", headers=headers).json()["data"]
    assert detail["status"] == "pending"
    assert detail["assigneeName"]
    assert any(log["action"] == "assign" for log in detail["logs"])
    assert detail["slaHours"] == 1


def test_resolve_requires_result_then_confirm_and_reopen(client):
    headers = auth_header(client, "admin")
    meta = _ids(client, headers)
    ticket_id = _create(client, headers, meta, title="需要解决").json()["data"]["id"]
    empty = client.post(
        f"/api/tickets/{ticket_id}/resolve", headers=headers, json={"resolution": "  "}
    )
    assert empty.json()["code"] == 400
    resolved = client.post(
        f"/api/tickets/{ticket_id}/resolve",
        headers=headers,
        json={"resolution": "已重置密码"},
    )
    assert resolved.json()["code"] == 200
    client.post(f"/api/tickets/{ticket_id}/confirm-request", headers=headers)
    admin_blocked = client.post(
        f"/api/tickets/{ticket_id}/confirm",
        headers=headers,
        json={"evaluation": "满意"},
    )
    assert admin_blocked.json()["code"] == 403
    customer_headers = auth_header(client, "customer01")
    closed = client.post(
        f"/api/tickets/{ticket_id}/customer-feedback",
        headers=customer_headers,
        json={"result": "confirmed", "remark": "满意", "rating": 5},
    )
    assert closed.json()["code"] == 200
    detail = client.get(f"/api/tickets/{ticket_id}", headers=headers).json()["data"]
    assert detail["status"] == "closed"
    assert detail["evaluation"] == "满意"
    blocked = client.post(
        f"/api/tickets/{ticket_id}/reopen",
        headers=headers,
        json={"reason": "问题仍在"},
    )
    assert blocked.json()["code"] == 400


def test_customer_cannot_create_and_workload_counts_assignee(client):
    denied = client.post(
        "/api/tickets",
        headers=auth_header(client, "customer01"),
        json={"title": "x", "description": "y"},
    )
    assert denied.json()["code"] == 403
    headers = auth_header(client, "admin")
    meta = _ids(client, headers)
    ticket_id = _create(client, headers, meta, title="待办统计").json()["data"]["id"]
    assignee = next(u for u in meta["users"] if u["name"] == "技术01")
    assigned = client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=headers,
        json={"assigneeId": assignee["id"], "groupId": _group_id(meta, "技术组")},
    )
    assert assigned.json()["code"] == 200
    detail = client.get(f"/api/tickets/{ticket_id}", headers=headers).json()["data"]
    assert detail["groupName"] == "技术组"
    workload = client.get("/api/tickets/workload", headers=headers).json()["data"]
    row = next(item for item in workload if item["userId"] == assignee["id"])
    assert row["pendingCount"] >= 1
    cs = next(u for u in meta["users"] if u["name"] == "客服01")
    transferred = client.post(
        f"/api/tickets/{ticket_id}/transfer",
        headers=headers,
        json={"assigneeId": cs["id"], "groupId": _group_id(meta, "客服组")},
    )
    assert transferred.json()["code"] == 200
    moved = client.get(f"/api/tickets/{ticket_id}", headers=headers).json()["data"]
    assert moved["assigneeName"] == "客服01"
    assert moved["groupName"] == "客服组"
    former_headers = auth_header(client, "tech01")
    former_detail = client.get(f"/api/tickets/{ticket_id}", headers=former_headers).json()
    assert former_detail["code"] == 200
    former_rows = client.get("/api/tickets", headers=former_headers).json()["data"]["records"]
    assert any(row["id"] == ticket_id for row in former_rows)
    former_status = client.post(
        f"/api/tickets/{ticket_id}/status",
        headers=former_headers,
        json={"status": "processing"},
    )
    assert former_status.json()["code"] == 403
    same = client.post(
        f"/api/tickets/{ticket_id}/transfer",
        headers=headers,
        json={"assigneeId": cs["id"], "groupId": _group_id(meta, "客服组")},
    )
    assert same.json()["code"] == 400
    assert "当前处理人" in same.json()["msg"]
    auto_id = _create(client, headers, meta, title="按组自动分配").json()["data"]["id"]
    auto = client.post(
        f"/api/tickets/{auto_id}/assign",
        headers=headers,
        json={"groupId": _group_id(meta, "技术组")},
    )
    assert auto.json()["code"] == 200
    auto_detail = client.get(f"/api/tickets/{auto_id}", headers=headers).json()["data"]
    assert auto_detail["assigneeName"] == "技术01"
    assert auto_detail["groupName"] == "技术组"


def test_escalate_only_when_overdue(client):
    headers = auth_header(client, "admin")
    meta = _ids(client, headers)
    ticket_id = _create(client, headers, meta, title="未超时").json()["data"]["id"]
    fresh = client.post(
        f"/api/tickets/{ticket_id}/escalate", headers=headers, json={"reason": "太慢"}
    )
    body = fresh.json()
    assert body["code"] == 400
    assert "超时" in body["msg"]


def test_group_has_single_leader_and_escalate_to_leader(client):
    from datetime import datetime, timedelta

    from app.db.session import get_db
    from app.main import app
    from app.models import Ticket

    admin_headers = auth_header(client, "admin")
    meta = _ids(client, admin_headers)
    groups = client.get("/api/handler-groups", headers=admin_headers).json()["data"]
    tech_group = next(item for item in groups if item["name"] == "技术组")
    assert tech_group["leaderName"] == "技术01"
    tech = next(u for u in meta["users"] if u["name"] == "技术01")
    cs = next(u for u in meta["users"] if u["name"] == "客服01")
    ticket_id = _create(client, admin_headers, meta, title="超时升级").json()["data"]["id"]
    client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": cs["id"], "groupId": _group_id(meta, "客服组")},
    )
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        ticket = db.get(Ticket, ticket_id)
        ticket.created_at = datetime.utcnow() - timedelta(hours=100)
        ticket.updated_at = ticket.created_at
        db.commit()
    finally:
        db.close()
    escalated = client.post(
        f"/api/tickets/{ticket_id}/escalate",
        headers=auth_header(client, "cs01"),
        json={"assigneeId": tech["id"], "reason": "需要技术处理"},
    )
    assert escalated.json()["code"] == 200
    detail = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert detail["assigneeName"] == "技术01"
    assert detail["groupName"] == "技术组"
    assert detail["status"] == "processing"
    assert detail["priorityName"] == "紧急"
    assert detail["slaState"] != "overdue"
    assert any(log["action"] == "escalate" for log in detail["logs"])
    client.post(
        f"/api/tickets/{ticket_id}/transfer",
        headers=admin_headers,
        json={"assigneeId": cs["id"], "groupId": _group_id(meta, "客服组")},
    )
    rows = client.get("/api/tickets", headers=admin_headers).json()["data"]["records"]
    tech_row = next(item for item in rows if item["id"] == ticket_id)
    assert tech_row["groupName"] == "客服组"

def test_unassigned_visible_only_to_admin_and_leaders(client):
    admin_headers = auth_header(client, "admin")
    meta = _ids(client, admin_headers)
    created = _create(client, admin_headers, meta, title="等待派发")
    ticket_id = created.json()["data"]["id"]
    tech_rows = client.get("/api/tickets", headers=auth_header(client, "tech01")).json()["data"]["records"]
    assert all(row["id"] != ticket_id for row in tech_rows)
    roles = client.get("/api/roles", headers=admin_headers, params={"page": 1, "pageSize": 50}).json()["data"]["records"]
    tech_role = next(item for item in roles if item["code"] == "tech")
    created_member = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "tech02", "displayName": "技术02", "roleIds": [tech_role["id"]]},
    )
    assert created_member.json()["code"] == 200
    member_token = client.post(
        "/api/auth/login",
        json={"username": "tech02", "password": md5_hex("admin123")},
    ).json()["data"]["token"]
    member_rows = client.get(
        "/api/tickets", headers={"Authorization": member_token}
    ).json()["data"]["records"]
    assert all(row["id"] != ticket_id for row in member_rows)
    admin_rows = client.get("/api/tickets", headers=admin_headers).json()["data"]["records"]
    assert any(row["id"] == ticket_id and row["status"] == "unassigned" for row in admin_rows)
    admin_user = next(u for u in meta["users"] if u["name"] == "管理员")
    rejected = client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": admin_user["id"], "groupId": _group_id(meta, "技术组")},
    )
    assert rejected.json()["code"] == 400
    tech = next(u for u in meta["users"] if u["name"] == "技术01")
    dispatched = client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": tech["id"], "groupId": _group_id(meta, "技术组")},
    )
    assert dispatched.json()["code"] == 200
    detail = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert detail["status"] == "pending"
    assert detail["assigneeName"] == "技术01"


def test_collaborator_can_view_with_lower_permission(client):
    admin_headers = auth_header(client, "admin")
    meta = _ids(client, admin_headers)
    ticket_id = _create(client, admin_headers, meta, title="协作权限").json()["data"]["id"]
    tech = next(u for u in meta["users"] if u["name"] == "技术01")
    customer = next(u for u in meta["users"] if u["name"] == "客户01")
    admin = next(u for u in meta["users"] if u["name"] == "管理员")
    assigned = client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": tech["id"], "groupId": _group_id(meta, "技术组")},
    )
    assert assigned.json()["code"] == 200
    customer_headers = auth_header(client, "customer01")
    before = client.get("/api/tickets", headers=customer_headers).json()["data"]["records"]
    assert all(row["id"] != ticket_id for row in before)
    rejected = client.put(
        f"/api/tickets/{ticket_id}/collaborators",
        headers=admin_headers,
        json={"userIds": [customer["id"]]},
    )
    assert rejected.json()["code"] == 400
    roles = client.get("/api/roles", headers=admin_headers, params={"page": 1, "pageSize": 50}).json()["data"]["records"]
    tech_role = next(item for item in roles if item["code"] == "tech")
    helper = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "helper01", "displayName": "协助01", "roleIds": [tech_role["id"]]},
    )
    assert helper.json()["code"] == 200
    helper_id = helper.json()["data"]["id"]
    collab = client.put(
        f"/api/tickets/{ticket_id}/collaborators",
        headers=admin_headers,
        json={"userIds": [helper_id]},
    )
    assert collab.json()["code"] == 200
    helper_token = client.post(
        "/api/auth/login",
        json={"username": "helper01", "password": md5_hex("admin123")},
    ).json()["data"]["token"]
    helper_headers = {"Authorization": helper_token}
    helper_rows = client.get("/api/tickets", headers=helper_headers).json()["data"]["records"]
    assert any(row["id"] == ticket_id for row in helper_rows)
    still_hidden = client.get("/api/tickets", headers=customer_headers).json()["data"]["records"]
    assert all(row["id"] != ticket_id for row in still_hidden)
    cs = next(u for u in meta["users"] if u["name"] == "客服01")
    moved = client.post(
        f"/api/tickets/{ticket_id}/transfer",
        headers=admin_headers,
        json={"assigneeId": cs["id"], "groupId": _group_id(meta, "技术组")},
    )
    assert moved.json()["code"] == 200
    detail = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert detail["assigneeName"] == "客服01"
    assert detail["groupName"] == "客服组"
    assert "协助01" in detail["collaboratorNames"]
    blocked = client.post(
        f"/api/tickets/{ticket_id}/transfer",
        headers=admin_headers,
        json={"assigneeId": admin["id"], "groupId": _group_id(meta, "管理组")},
    )
    assert blocked.json()["code"] == 400
    assert "升级" in blocked.json()["msg"]
    visible = client.get("/api/tickets", headers=helper_headers).json()["data"]["records"]
    row = next(item for item in visible if item["id"] == ticket_id)
    assert "协助01" in row["collaboratorNames"]
    assert row["createdAt"]
    assert row["updatedAt"]
    tech_headers = auth_header(client, "tech01")
    started = client.post(
        f"/api/tickets/{ticket_id}/status",
        headers=auth_header(client, "cs01"),
        json={"status": "processing"},
    )
    assert started.json()["code"] == 200
    denied_start = client.post(
        f"/api/tickets/{ticket_id}/status",
        headers=tech_headers,
        json={"status": "waiting_customer"},
    )
    assert denied_start.json()["code"] == 403
    denied_note = client.post(
        f"/api/tickets/{ticket_id}/notes",
        headers=tech_headers,
        json={"content": "协助补充日志"},
    )
    assert denied_note.json()["code"] == 403
    transferred = client.post(
        f"/api/tickets/{ticket_id}/transfer",
        headers=tech_headers,
        json={"groupId": _group_id(meta, "技术组")},
    )
    assert transferred.json()["code"] == 403
    count = client.get("/api/tickets/pending-count", headers=admin_headers).json()["data"]["count"]
    listed = client.get(
        "/api/tickets",
        headers=admin_headers,
        params={"page": 1, "pageSize": 100},
    ).json()["data"]["records"]
    expect = sum(1 for row in listed if row["status"] in {"unassigned", "pending"})
    assert count == expect
    tech_count = client.get("/api/tickets/pending-count", headers=tech_headers).json()["data"]["count"]
    tech_listed = client.get("/api/tickets", headers=tech_headers, params={"page": 1, "pageSize": 100}).json()["data"]["records"]
    expect_tech = sum(1 for row in tech_listed if row["status"] == "pending")
    assert tech_count == expect_tech


def test_group_member_cannot_see_other_handlers(client):
    admin_headers = auth_header(client, "admin")
    meta = _ids(client, admin_headers)
    roles = client.get("/api/roles", headers=admin_headers, params={"page": 1, "pageSize": 50}).json()["data"]["records"]
    cs_role = next(item for item in roles if item["code"] == "cs")
    created = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "003", "displayName": "客服003", "roleIds": [cs_role["id"]]},
    )
    assert created.json()["code"] == 200
    ticket_id = _create(client, admin_headers, meta, title="别人的工单").json()["data"]["id"]
    cs = next(u for u in meta["users"] if u["name"] == "客服01")
    assigned = client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": cs["id"], "groupId": _group_id(meta, "客服组")},
    )
    assert assigned.json()["code"] == 200
    member = client.post(
        "/api/auth/login",
        json={"username": "003", "password": md5_hex("admin123")},
    ).json()["data"]["token"]
    member_headers = {"Authorization": member}
    rows = client.get("/api/tickets", headers=member_headers).json()["data"]["records"]
    assert all(row["id"] != ticket_id for row in rows)
    hidden = client.get(f"/api/tickets/{ticket_id}", headers=member_headers).json()
    assert hidden["code"] == 403
    leader_rows = client.get("/api/tickets", headers=auth_header(client, "cs01")).json()["data"]["records"]
    assert any(row["id"] == ticket_id for row in leader_rows)
    assignee_rows = client.get("/api/tickets", headers=auth_header(client, "cs01")).json()["data"]["records"]
    assert any(row["id"] == ticket_id and row["assigneeName"] == "客服01" for row in assignee_rows)
    tech_rows = client.get("/api/tickets", headers=auth_header(client, "tech01")).json()["data"]["records"]
    assert all(row["id"] != ticket_id for row in tech_rows)


def test_customer_ask_waiting_feedback_and_close(client):
    admin_headers = auth_header(client, "admin")
    meta = _ids(client, admin_headers)
    customer_headers = auth_header(client, "customer01")
    asked = client.post(
        "/api/tickets/ask",
        headers=customer_headers,
        json={
            "title": "客户提问一",
            "description": "视频打不开",
            "categoryId": meta["categoryId"],
            "priorityId": meta["priorityId"],
            "product": "工单系统",
            "serviceName": "账号服务",
        },
    )
    assert asked.json()["code"] == 200
    ticket_id = asked.json()["data"]["id"]
    asked_detail = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert asked_detail["sourceLabel"] == "客户提问"
    staff = _create(client, admin_headers, meta, title="后台工单")
    assert staff.json()["code"] == 200
    staff_id = staff.json()["data"]["id"]
    staff_detail = client.get(
        f"/api/tickets/{staff_id}", headers=admin_headers
    ).json()["data"]
    assert staff_detail["sourceLabel"] == "后台创建"
    mine = client.get("/api/tickets/mine", headers=customer_headers).json()["data"]["records"]
    assert any(row["id"] == ticket_id and row["status"] == "unassigned" for row in mine)
    assert any(row["id"] == staff_id for row in mine)
    admin_mine = client.get("/api/tickets/mine", headers=admin_headers).json()["data"]["records"]
    assert any(row["id"] == ticket_id for row in admin_mine)
    assert all(row["id"] != staff_id for row in admin_mine)
    unbound = client.post(
        "/api/customers",
        headers=admin_headers,
        json={
            "name": "未绑定客户",
            "contactName": "无人",
            "phone": "13900000000",
            "email": "none@example.com",
            "industry": "教育",
            "status": 1,
        },
    ).json()["data"]
    rejected = _create(client, admin_headers, {**meta, "customerId": unbound["id"]}, title="无账号工单")
    assert rejected.json()["code"] == 400
    assert "绑定" in rejected.json()["msg"]
    cs_created = _create(client, auth_header(client, "cs01"), meta, title="客服代提")
    assert cs_created.json()["code"] == 200
    assert any(
        row["id"] == cs_created.json()["data"]["id"]
        for row in client.get("/api/tickets/mine", headers=customer_headers).json()["data"]["records"]
    )
    tech_member = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "tech03",
            "displayName": "技术03",
            "roleIds": [
                next(
                    item["id"]
                    for item in client.get(
                        "/api/roles", headers=admin_headers, params={"page": 1, "pageSize": 50}
                    ).json()["data"]["records"]
                    if item["code"] == "tech"
                )
            ],
        },
    )
    assert tech_member.json()["code"] == 200
    member_token = client.post(
        "/api/auth/login",
        json={"username": "tech03", "password": md5_hex("admin123")},
    ).json()["data"]["token"]
    hidden = client.get(
        "/api/tickets", headers={"Authorization": member_token}
    ).json()["data"]["records"]
    assert all(row["id"] != ticket_id for row in hidden)
    tech = next(u for u in meta["users"] if u["name"] == "技术01")
    client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": tech["id"], "groupId": _group_id(meta, "技术组")},
    )
    client.post(
        f"/api/tickets/{ticket_id}/status",
        headers=auth_header(client, "tech01"),
        json={"status": "processing"},
    )
    replied = client.post(
        f"/api/tickets/{ticket_id}/handle-reply",
        headers=auth_header(client, "tech01"),
        json={"reply": "已定位原因", "solution": "请刷新后重试", "internalNote": "内部排查记录"},
    )
    assert replied.json()["code"] == 200
    started = client.get(f"/api/tickets/{ticket_id}", headers=customer_headers).json()["data"]
    assert started["status"] == "processing"
    assert started["slaState"] != "paused"
    continued = client.post(
        f"/api/tickets/{ticket_id}/handle-reply",
        headers=auth_header(client, "tech01"),
        json={"reply": "再写一次", "solution": "还不行"},
    )
    assert continued.json()["code"] == 200
    still = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert still["status"] == "processing"
    visible = client.get("/api/tickets/mine", headers=customer_headers).json()["data"]["records"]
    assert any(row["id"] == ticket_id and row["statusLabel"] == "处理中" for row in visible)
    shown = client.get(f"/api/tickets/{ticket_id}", headers=customer_headers).json()["data"]
    assert shown["handlerReply"] == "再写一次"
    assert shown["handlerSolution"] == "还不行"
    assert all(item["action"] != "internal" for item in shown["logs"])
    empty_reject = client.post(
        f"/api/tickets/{ticket_id}/customer-feedback",
        headers=customer_headers,
        json={"result": "rejected", "remark": ""},
    )
    assert empty_reject.json()["code"] == 400
    waiting = client.post(
        f"/api/tickets/{ticket_id}/status",
        headers=auth_header(client, "tech01"),
        json={"status": "waiting_customer"},
    )
    assert waiting.json()["code"] == 200
    supplemented = client.post(
        f"/api/tickets/{ticket_id}/customer-feedback",
        headers=customer_headers,
        json={"result": "supplement", "remark": "补充了截图"},
    )
    assert supplemented.json()["code"] == 200
    back = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert back["status"] == "processing"
    from datetime import datetime, timedelta

    from app.db.session import get_db
    from app.main import app
    from app.models import Ticket

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        ticket = db.get(Ticket, ticket_id)
        ticket.status = "overdue"
        ticket.created_at = datetime.utcnow() - timedelta(hours=100)
        ticket.sla_started_at = ticket.created_at
        db.commit()
    finally:
        db_gen.close()
    repaired = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert repaired["status"] == "processing"
    solved_denied = client.post(
        f"/api/tickets/{ticket_id}/customer-feedback",
        headers=customer_headers,
        json={"result": "solved", "remark": "已经好了"},
    )
    assert solved_denied.json()["code"] == 400
    marked = client.post(
        f"/api/tickets/{ticket_id}/status",
        headers=auth_header(client, "tech01"),
        json={"status": "resolved"},
    )
    assert marked.json()["code"] == 200
    assert (
        client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]["statusLabel"]
        == "已解决"
    )
    reopened = client.post(
        f"/api/tickets/{ticket_id}/customer-feedback",
        headers=customer_headers,
        json={"result": "rejected", "remark": "还是不行"},
    )
    assert reopened.json()["code"] == 200
    assert (
        client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]["status"]
        == "reopened"
    )
    continued_again = client.post(
        f"/api/tickets/{ticket_id}/handle-reply",
        headers=auth_header(client, "tech01"),
        json={"reply": "已按反馈调整", "solution": "请再试一次"},
    )
    assert continued_again.json()["code"] == 200
    assert (
        client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]["status"]
        == "reopened"
    )
    client.post(
        f"/api/tickets/{ticket_id}/status",
        headers=auth_header(client, "tech01"),
        json={"status": "resolved"},
    )
    confirmed = client.post(
        f"/api/tickets/{ticket_id}/customer-feedback",
        headers=customer_headers,
        json={"result": "confirmed", "remark": "可以了", "rating": 4},
    )
    assert confirmed.json()["code"] == 200
    assert (
        client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]["status"]
        == "closed"
    )
    staff_reopen = client.post(
        f"/api/tickets/{ticket_id}/reopen",
        headers=auth_header(client, "tech01"),
        json={"reason": "再看一次"},
    )
    assert staff_reopen.json()["code"] == 400
    still_listed = client.get("/api/tickets/mine", headers=customer_headers).json()["data"]["records"]
    assert any(row["id"] == ticket_id and row["status"] == "closed" for row in still_listed)


def test_cs_followup_on_closed_ticket(client):
    admin_headers = auth_header(client, "admin")
    customer_headers = auth_header(client, "customer01")
    cs_headers = auth_header(client, "cs01")
    meta = _ids(client, admin_headers)
    ticket_id = _create(client, admin_headers, meta, title="待回访工单").json()["data"]["id"]
    tech = next(u for u in meta["users"] if u["name"] == "技术01")
    client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": tech["id"], "groupId": _group_id(meta, "技术组")},
    )
    client.post(
        f"/api/tickets/{ticket_id}/status",
        headers=auth_header(client, "tech01"),
        json={"status": "processing"},
    )
    client.post(
        f"/api/tickets/{ticket_id}/status",
        headers=auth_header(client, "tech01"),
        json={"status": "resolved"},
    )
    closed = client.post(
        f"/api/tickets/{ticket_id}/customer-feedback",
        headers=customer_headers,
        json={"result": "confirmed", "remark": "好了"},
    )
    assert closed.json()["code"] == 200

    open_id = _create(client, admin_headers, meta, title="未关闭不可回访").json()["data"]["id"]
    blocked_open = client.post(
        f"/api/tickets/{open_id}/followup",
        headers=admin_headers,
        json={"method": "电话", "result": "满意", "remark": "x"},
    )
    assert blocked_open.json()["code"] == 400
    assert "关闭" in blocked_open.json()["msg"]

    tech_denied = client.post(
        f"/api/tickets/{ticket_id}/followup",
        headers=auth_header(client, "tech01"),
        json={"method": "微信", "result": "一般", "remark": "技术不可回访"},
    )
    assert tech_denied.json()["code"] in (403, 401)

    customer_denied = client.post(
        f"/api/tickets/{ticket_id}/followup",
        headers=customer_headers,
        json={"method": "电话", "result": "满意"},
    )
    assert customer_denied.json()["code"] in (403, 401)

    saved = client.post(
        f"/api/tickets/{ticket_id}/followup",
        headers=cs_headers,
        json={
            "method": "微信",
            "result": "问题复发",
            "remark": "客户反馈偶发仍打不开",
            "followupAt": "2026-09-22 10:30:00",
        },
    )
    assert saved.json()["code"] == 200
    detail = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert detail["followedUp"] is True
    assert detail["followupMethod"] == "微信"
    assert detail["followupResult"] == "问题复发"
    assert detail["followupRemark"] == "客户反馈偶发仍打不开"
    assert detail["followupUserName"]
    assert any(log["action"] == "followup" for log in detail["logs"])

    customer_detail = client.get(f"/api/tickets/{ticket_id}", headers=customer_headers).json()["data"]
    assert "followupResult" not in customer_detail
    assert "followedUp" not in customer_detail
    assert all(log["action"] != "followup" for log in customer_detail["logs"])

    listed = client.get(
        "/api/tickets", headers=cs_headers, params={"status": "closed"}
    ).json()["data"]["records"]
    row = next(item for item in listed if item["id"] == ticket_id)
    assert row["followedUp"] is True


def test_priority_sla_hours(client):
    headers = auth_header(client, "admin")
    options = client.get("/api/tickets/options", headers=headers).json()["data"]
    by_name = {p["name"]: p for p in options["priorities"]}
    assert by_name["紧急"]["slaHours"] == 1
    assert by_name["高"]["slaHours"] == 4


def test_auto_escalate_on_list_when_overdue(client):
    from datetime import datetime, timedelta
    from app.db.session import get_db
    from app.main import app
    from app.models import Ticket

    admin_headers = auth_header(client, "admin")
    meta = _ids(client, admin_headers)
    roles = client.get("/api/roles", headers=admin_headers, params={"page": 1, "pageSize": 50}).json()["data"]["records"]
    tech_role = next(item for item in roles if item["code"] == "tech")
    created_user = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "tech_member_esc", "displayName": "技术组员", "roleIds": [tech_role["id"]]},
    )
    assert created_user.json()["code"] == 200
    member_id = created_user.json()["data"]["id"]
    ticket_id = _create(client, admin_headers, meta, title="自动升级").json()["data"]["id"]
    client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": member_id, "groupId": _group_id(meta, "技术组")},
    )
    db = next(app.dependency_overrides[get_db]())
    try:
        ticket = db.get(Ticket, ticket_id)
        ticket.sla_started_at = datetime.utcnow() - timedelta(hours=3)
        ticket.created_at = ticket.sla_started_at
        db.commit()
    finally:
        db.close()
    detail = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert detail["assigneeName"] == "技术01"
    assert any(log["action"] == "escalate" for log in detail["logs"])


def test_auto_escalate_leader_to_admin(client):
    from datetime import datetime, timedelta
    from app.db.session import get_db
    from app.main import app
    from app.models import Ticket

    admin_headers = auth_header(client, "admin")
    meta = _ids(client, admin_headers)
    tech = next(u for u in meta["users"] if u["name"] == "技术01")
    ticket_id = _create(client, admin_headers, meta, title="组长超时升管理员").json()["data"]["id"]
    client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": tech["id"], "groupId": _group_id(meta, "技术组")},
    )
    db = next(app.dependency_overrides[get_db]())
    try:
        ticket = db.get(Ticket, ticket_id)
        ticket.sla_started_at = datetime.utcnow() - timedelta(hours=3)
        ticket.created_at = ticket.sla_started_at
        db.commit()
    finally:
        db.close()
    detail = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert detail["assigneeName"] == "管理员"


def test_my_overdue_count_before_escalate(client):
    from datetime import datetime, timedelta
    from app.db.session import get_db
    from app.main import app
    from app.models import Ticket

    admin_headers = auth_header(client, "admin")
    meta = _ids(client, admin_headers)
    tech = next(u for u in meta["users"] if u["name"] == "技术01")
    ticket_id = _create(client, admin_headers, meta, title="超时计数").json()["data"]["id"]
    client.post(
        f"/api/tickets/{ticket_id}/assign",
        headers=admin_headers,
        json={"assigneeId": tech["id"], "groupId": _group_id(meta, "技术组")},
    )
    db = next(app.dependency_overrides[get_db]())
    try:
        ticket = db.get(Ticket, ticket_id)
        ticket.sla_started_at = datetime.utcnow() - timedelta(hours=3)
        ticket.created_at = ticket.sla_started_at
        db.commit()
    finally:
        db.close()
    tech_headers = auth_header(client, "tech01")
    data = client.get("/api/tickets/pending-count", headers=tech_headers).json()["data"]
    assert data["myOverdueCount"] >= 1
    admin_data = client.get("/api/tickets/pending-count", headers=admin_headers).json()["data"]
    assert "myOverdueCount" in admin_data
