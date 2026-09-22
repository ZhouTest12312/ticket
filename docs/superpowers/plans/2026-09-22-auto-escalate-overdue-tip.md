# Auto-Escalate & Overdue Tip Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adjust SLA hours (紧急 1h / 高 4h), auto-escalate overdue tickets to group leader (or admin), and show a non-auto-closing global tip for “我的待处理超时工单”.

**Architecture:** Lazy sync on ticket read APIs: count the current user’s overdue assigned tickets first, then auto-escalate any overdue open tickets using the same rules as manual escalate. Frontend layout polls/fetches that count and shows `ElNotification` with `duration: 0`, re-showing only when the count changes after dismiss.

**Tech Stack:** FastAPI, SQLAlchemy, Vue3, Element Plus (`ElNotification`), existing `sla_info` / escalate helpers.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-22-auto-escalate-overdue-tip-design.md`
- Do not add a background cron job
- Do not change 中/低 SLA values (24h / 72h)
- Do not commit unless the user explicitly asks
- Customers must not see the overdue tip
- Auto-escalate target: group leader; if assignee is already leader → admin

## File Map

| File | Responsibility |
|------|----------------|
| `server/scripts/seed_data.py` | PRIORITIES sla_hours 紧急=1, 高=4 |
| `server/app/api/tickets.py` | `_auto_escalate_ticket`, sync hook, `myOverdueCount` on pending-count |
| `server/tests/test_tickets.py` | Auto-escalate + overdue count tests |
| `src/api/ticket/index.js` | Expose overdue count from pending-count |
| `src/layout/index.vue` | Global overdue `ElNotification` |

---

### Task 1: SLA seed hours

**Files:**
- Modify: `server/scripts/seed_data.py` (`PRIORITIES`)
- Test: `server/tests/test_tickets.py`

**Interfaces:**
- Produces: seed rows 紧急 `sla_hours=1`, 高 `sla_hours=4` (seed already overwrites existing rows)

- [ ] **Step 1: Write failing assertion on options priorities**

Add to `server/tests/test_tickets.py`:

```python
def test_priority_sla_hours(client):
    headers = auth_header(client, "admin")
    options = client.get("/api/tickets/options", headers=headers).json()["data"]
    by_name = {p["name"]: p for p in options["priorities"]}
    assert by_name["紧急"]["slaHours"] == 1
    assert by_name["高"]["slaHours"] == 4
```

- [ ] **Step 2: Run test — expect FAIL if still 2/8**

```bash
cd server
.\.venv\Scripts\python.exe -m pytest tests\test_tickets.py::test_priority_sla_hours -v --tb=short
```

- [ ] **Step 3: Update PRIORITIES**

In `server/scripts/seed_data.py`:

```python
PRIORITIES = [
    ("低", 1, 72, 8),
    ("中", 2, 24, 4),
    ("高", 3, 4, 1),
    ("紧急", 4, 1, 0),
]
```

(`warn_hours` for 紧急 can be 0; 高 warn 1 hour before deadline.)

- [ ] **Step 4: Re-run test — PASS**

Also update `test_create_assign_and_logs` if it asserts `slaHours == 2` for the priority used in `_ids` (last priority is 紧急) — change expectation to `1`.

---

### Task 2: Auto-escalate on read sync

**Files:**
- Modify: `server/app/api/tickets.py`
- Test: `server/tests/test_tickets.py`

**Interfaces:**
- Produces: `_apply_escalate(db, ticket, operator=None, reason=...)` mutating ticket; `_sync_overdue_and_escalate(db, tickets)` 
- Consumes: existing `_set_status`, `_add_log`, `_remember_former_assignee`, `sla_info`, HandlerGroup / Role / User / TicketPriority

- [ ] **Step 1: Failing test — list/get triggers escalate**

```python
def test_auto_escalate_on_list_when_overdue(client):
    from datetime import datetime, timedelta
    from app.db.session import get_db
    from app.main import app
    from app.models import Ticket

    admin_headers = auth_header(client, "admin")
    meta = _ids(client, admin_headers)
    tech = next(u for u in meta["users"] if u["name"] == "技术01")
    # assign to non-leader member of 技术组 if possible; else use cs in 客服组
    cs = next(u for u in meta["users"] if u["name"] == "客服01")
    # create member under 客服组 who is not leader — reuse pattern from collab test OR assign tech to 技术组 where leader is tech01
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
    # trigger sync via get
    detail = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()["data"]
    assert detail["assigneeName"] == "技术01"  # group leader
    assert any(log["action"] == "escalate" for log in detail["logs"])
```

- [ ] **Step 2: Run — FAIL (no auto escalate yet)**

- [ ] **Step 3: Implement helpers and wire sync**

Extract escalate body from `escalate_ticket` into:

```python
def _resolve_escalate_target(db: Session, ticket: Ticket) -> User | None:
    ...


def _apply_escalate(
    db: Session,
    ticket: Ticket,
    *,
    operator: User | None,
    reason: str = "处理超时，系统自动升级给负责人",
) -> bool:
    """Returns True if escalated. Skips if not overdue."""
    if ticket.status in {"resolved", "closed", "ended", "unassigned"}:
        return False
    if ticket.status == "waiting_customer":
        return False
    if sla_info(ticket)["slaState"] != "overdue":
        return False
    target = _resolve_escalate_target(db, ticket)
    if not target:
        return False
    # same assignee/group/priority/sla/status/log as current escalate_ticket
    ...
    return True
```

Replace `_sync_overdue` usage sites that load tickets with:

```python
def _sync_sla(db: Session, tickets: list[Ticket]) -> bool:
    changed = False
    # keep existing overdue→processing-when-customer-replied logic if still needed
    for ticket in tickets:
        if _apply_escalate(db, ticket, operator=None):
            changed = True
    if changed:
        db.commit()
    return changed
```

Call `_sync_sla` from `list_tickets`, `get_ticket`, and `pending_count` (before counting).

Refactor manual `escalate_ticket` to call `_apply_escalate` after permission checks (manual may still require overdue check and allow custom assigneeId — keep existing body for assignee override).

- [ ] **Step 4: Run auto-escalate test — PASS**

- [ ] **Step 5: Extra test — leader assignee escalates to admin**

```python
def test_auto_escalate_leader_to_admin(client):
    # assign to 技术01 (技术组 leader), backdate sla, get ticket as admin
    # expect assigneeName == 管理员
```

---

### Task 3: `myOverdueCount` API

**Files:**
- Modify: `server/app/api/tickets.py` (`pending_count`)
- Modify: `src/api/ticket/index.js`
- Test: `server/tests/test_tickets.py`

**Interfaces:**
- Produces: `GET /api/tickets/pending-count` → `{ count, myOverdueCount }`
- Spec order: compute `myOverdueCount` **before** auto-escalate; then run `_sync_sla`

- [ ] **Step 1: Failing test**

```python
def test_my_overdue_count_before_escalate(client):
    # create ticket assigned to tech01, backdate sla so overdue
    # GET pending-count as tech01 → myOverdueCount >= 1
    # GET again as admin → myOverdueCount for admin may be 0 unless admin is assignee
```

- [ ] **Step 2: Implement pending_count**

```python
@router.get("/tickets/pending-count")
def pending_count(...):
    # existing count logic for menu badge...
    my_overdue = 0
    if user.id:
        mine = (
            db.query(Ticket)
            .filter(
                Ticket.assignee_id == user.id,
                Ticket.status.in_(["pending", "processing", "overdue", "reopened"]),
            )
            .all()
        )
        my_overdue = sum(1 for t in mine if sla_info(t)["slaState"] == "overdue")
        _sync_sla(db, mine)  # and optionally broader open set for escalate
    # Also sync a broader open-ticket set so escalate happens even when viewing as admin:
    # open = db.query(Ticket).filter(Ticket.status.in_(OPEN)).all(); _sync_sla(db, open)
    return ok({"count": count, "myOverdueCount": my_overdue})
```

For list/get: call `_sync_sla` as today.

- [ ] **Step 3: Frontend API**

```javascript
export async function ticketPendingCount() {
  return unwrap(await request.get('/tickets/pending-count'));
}

export async function refreshTicketMenuBadge() {
  try {
    const data = await ticketPendingCount();
    setMenuBadge('/ticket/list', Number(data?.count) || 0);
    return data;
  } catch (_) {
    return { count: 0, myOverdueCount: 0 };
  }
}
```

- [ ] **Step 4: Tests PASS**

---

### Task 4: Global overdue notification

**Files:**
- Modify: `src/layout/index.vue`

**Interfaces:**
- Consumes: `refreshTicketMenuBadge()` / `ticketPendingCount()` → `myOverdueCount`
- Session key: `ticket_overdue_tip_dismissed_count`

- [ ] **Step 1: Add tip helper in layout `onMounted` (ticket brand only)**

```javascript
import { ElNotification } from 'element-plus';

const OVERDUE_TIP_KEY = 'ticket_overdue_tip_dismissed_count';

const showOverdueTip = (count) => {
  if (!count || count <= 0) return;
  const dismissed = Number(sessionStorage.getItem(OVERDUE_TIP_KEY) || '');
  if (dismissed === count) return;
  ElNotification({
    title: '超时提醒',
    message: `我的待处理超时工单：${count}`,
    type: 'warning',
    duration: 0,
    position: 'top-right',
    onClose: () => {
      sessionStorage.setItem(OVERDUE_TIP_KEY, String(count));
    },
  });
};

onMounted(async () => {
  // existing...
  if (isTicketBrand.value) {
    const data = await refreshTicketMenuBadge();
    const roles = userStore.roles || [];
    if (!roles.includes('customer')) {
      showOverdueTip(Number(data?.myOverdueCount) || 0);
    }
  }
});
```

Optional: also call when `refreshTicketMenuBadge` runs after ticket actions — not required for MVP if layout remount is rare; call `showOverdueTip` from `refreshTicketMenuBadge` side-effect only in layout is enough for login entry. Add a small interval (e.g. 60s) **or** re-check on `visibilitychange` — spec allows optional; implement `document.addEventListener('visibilitychange', ...)` when visible again.

- [ ] **Step 2: Manual check** — login as assignee with overdue ticket, see sticky notification; close; same count no re-show; change count (another overdue) re-shows.

---

### Task 5: Regression

- [ ] **Step 1: Run full ticket tests**

```bash
cd server
.\.venv\Scripts\python.exe -m pytest tests\test_tickets.py -v --tb=short
```

Expected: all PASS

- [ ] **Step 2: Spec coverage check**
  - SLA 1h/4h → Task 1
  - Auto escalate all priorities → Task 2
  - Leader → admin → Task 2 step 5
  - myOverdueCount before escalate → Task 3
  - Global tip dismiss-by-count → Task 4

---

## Spec Coverage Self-Review

| Spec item | Task |
|-----------|------|
| 紧急1h / 高4h seed | 1 |
| Auto escalate on lazy sync | 2 |
| Target leader / admin | 2 |
| myOverdueCount before escalate | 3 |
| ElNotification duration 0 + recount re-show | 4 |
| No cron / no customer tip | 2–4 |
| Manual escalate kept | 2 (refactor) |
