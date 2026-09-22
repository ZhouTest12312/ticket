# Role Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver OpenSpec-backed RBAC (roles/permissions/user assignment) with FastAPI+MySQL backend, Vue role UI, JWT login, and Vite proxy to local `:8000`.

**Architecture:** Classic RBAC in `server/` (users↔roles↔permissions). Frontend keeps existing axios/`Authorization` patterns; `devLocal` proxies `/api` to FastAPI. `/api/auth/me` returns permissions plus static-style menus so Layout can register `/system/role` and `/system/user-role` without remote accesscenter.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, PyMySQL, python-jose, passlib[bcrypt], pytest; Vue3 + Element Plus + Ele Admin Plus; OpenSpec CLI; MySQL database `ticket_support`.

**Spec:** `docs/superpowers/specs/2026-09-20-role-management-design.md`

## Global Constraints

- Response envelope: `{ "code": 200|4xx, "data": ..., "msg": "..." }` — success `code` must be `200`.
- 403 `msg`: Chinese, at least `当前没有权限执行此操作`.
- 401 `msg`: `请先登录`.
- JWT in `Authorization` header; accept raw token or `Bearer <token>`.
- System roles (`admin`,`cs`,`tech`,`customer`): editable permissions, **not** deletable.
- Seed password: `Admin@123` for `admin` / `cs01` / `tech01` / `customer01`.
- Do **not** implement ticket CRUD/SLA in this plan (permission codes only).
- Do **not** `git commit` unless the user explicitly asks (ignore per-task commit checkboxes until then).
- Follow `CONTRACT.md` for frontend API modules.

## File Structure (target)

```
super-campus/
├── openspec/
│   ├── AGENTS.md
│   ├── project.md
│   ├── specs/                    # empty until archive
│   └── changes/role-management/
│       ├── proposal.md
│       ├── design.md
│       ├── tasks.md
│       └── specs/
│           ├── auth/spec.md
│           └── rbac/spec.md
├── server/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   ├── auth.py
│   │   │   ├── roles.py
│   │   │   ├── users.py
│   │   │   └── permissions.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── response.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── role.py
│   │   │   └── permission.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── role.py
│   │   │   └── user.py
│   │   └── services/
│   │       ├── auth_service.py
│   │       ├── role_service.py
│   │       └── user_service.py
│   ├── scripts/
│   │   ├── init_db.py
│   │   └── seed.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_roles.py
│   │   └── test_users.py
│   ├── requirements.txt
│   ├── .env.example
│   └── CONTRACT.md
├── src/api/ticketAuth/index.js
├── src/api/role/index.js
├── src/api/userRole/index.js
├── src/views/system/role/index.vue
├── src/views/system/role/components/role-edit-drawer.vue
├── src/views/system/user-role/index.vue
├── src/views/system/user-role/components/assign-role-drawer.vue
├── src/config/ticket-menus.js
├── .env.devLocal                          # proxy target
└── vite.config.js                         # /api → FastAPI when flagged
```

---

### Task 1: OpenSpec init + role-management change artifacts

**Files:**
- Create: `openspec/project.md`, `openspec/AGENTS.md` (via CLI), `openspec/changes/role-management/**`
- Modify: none required in app code

**Interfaces:**
- Produces: change id `role-management` with proposal/design/specs/tasks for later `/opsx:apply` alignment

- [ ] **Step 1: Install OpenSpec CLI if missing**

```bash
npm install -g @fission-ai/openspec@latest
openspec --version
```

Expected: prints a version (e.g. `1.x.x`).

- [ ] **Step 2: Initialize OpenSpec in repo root**

```bash
cd "d:/workspace/新建文件夹/super-campus"
openspec init --yes
```

If `--yes` unsupported, run `openspec init` and choose Cursor when prompted. Expected: `openspec/` directory exists.

- [ ] **Step 3: Create change folder + proposal**

Create `openspec/changes/role-management/proposal.md`:

```markdown
# Proposal: role-management

## Why
Need configurable RBAC before ticket lifecycle so admin/cs/tech/customer capabilities are data-driven.

## What Changes
- FastAPI server with JWT auth and RBAC APIs
- Vue role + user-role pages
- Vite proxy to local backend
- Seed four system roles and demo users

## Out of Scope
Ticket CRUD, SLA, customer management UI, remote uber usercenter.
```

- [ ] **Step 4: Write delta specs**

Create `openspec/changes/role-management/specs/auth/spec.md`:

```markdown
## ADDED Requirements

### Requirement: Password login issues JWT
The system SHALL authenticate username/password and return a JWT plus user summary in `{code,data,msg}` with `code=200` on success.

#### Scenario: Valid credentials
- **WHEN** client POSTs `/api/auth/login` with valid username and password
- **THEN** response `code` is 200 and `data.token` is a non-empty string

#### Scenario: Invalid credentials
- **WHEN** password is wrong
- **THEN** response `code` is 400 or 401 and `msg` is Chinese

### Requirement: Current user profile
The system SHALL expose `/api/auth/me` requiring a valid JWT and returning roles, permission codes, and menus.

#### Scenario: Missing token
- **WHEN** Authorization header is absent
- **THEN** `code` is 401 and `msg` is `请先登录`
```

Create `openspec/changes/role-management/specs/rbac/spec.md`:

```markdown
## ADDED Requirements

### Requirement: Role CRUD with permission binding
Admins with `role:write` SHALL create/update/delete roles and bind permission ids. System roles SHALL NOT be deleted.

#### Scenario: Delete system role rejected
- **WHEN** client deletes role `admin`
- **THEN** `code` is 400 and body explains system role cannot be deleted

#### Scenario: Forbidden without permission
- **WHEN** a user lacking `role:write` POSTs `/api/roles`
- **THEN** `code` is 403 and `msg` contains `当前没有权限执行此操作`

### Requirement: Assign roles to users
Users with `user:assign_role` SHALL replace a user's role set via `PUT /api/users/{id}/roles`.
```

- [ ] **Step 5: Copy design summary + tasks checklist**

Create `openspec/changes/role-management/design.md` as a short pointer to `docs/superpowers/specs/2026-09-20-role-management-design.md` plus API table from that spec.

Create `openspec/changes/role-management/tasks.md` listing Tasks 2–10 from this plan as checkboxes.

- [ ] **Step 6: Validate**

```bash
openspec validate role-management --strict
```

Expected: pass (or fix structural issues until pass).

---

### Task 2: FastAPI project skeleton + response helpers

**Files:**
- Create: `server/requirements.txt`, `server/.env.example`, `server/app/main.py`, `server/app/core/config.py`, `server/app/core/response.py`, `server/app/db/base.py`, `server/app/db/session.py`, `server/CONTRACT.md`
- Test: `server/tests/test_health.py`

**Interfaces:**
- Produces: `Settings` from env; `ok(data, msg="ok")` / `fail(code, msg)`; `get_db()` generator; app on port 8000 with `GET /api/health`

- [ ] **Step 1: Write requirements.txt**

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
pymysql==1.1.1
cryptography==44.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
pydantic-settings==2.7.0
python-multipart==0.0.20
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 2: Write `.env.example`**

```env
APP_NAME=ticket-support
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ticket_support
JWT_SECRET=change-me-in-local-dev
JWT_EXPIRE_HOURS=24
```

- [ ] **Step 3: Implement config + response + db session**

`server/app/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "ticket-support"
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "ticket_support"
    jwt_secret: str = "change-me"
    jwt_expire_hours: int = 24

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

settings = Settings()
```

`server/app/core/response.py`:

```python
from typing import Any
from fastapi.responses import JSONResponse

def envelope(code: int, data: Any = None, msg: str = "ok") -> dict:
    return {"code": code, "data": data, "msg": msg}

def ok(data: Any = None, msg: str = "ok") -> dict:
    return envelope(200, data, msg)

def fail_response(code: int, msg: str) -> JSONResponse:
    return JSONResponse(status_code=200, content=envelope(code, None, msg))
```

Note: keep HTTP 200 with business `code` field to match existing frontend interceptors that read `res.data.code`.

`server/app/db/session.py`: engine + `SessionLocal` + `get_db()`.

- [ ] **Step 4: `main.py` with health**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.response import ok

app = FastAPI(title="ticket-support")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return ok({"status": "up"})
```

- [ ] **Step 5: Write failing/passing health test**

`server/tests/test_health.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 200
    assert body["data"]["status"] == "up"
```

- [ ] **Step 6: Run test**

```bash
cd server
pip install -r requirements.txt
pytest tests/test_health.py -v
```

Expected: PASS.

- [ ] **Step 7: Write `server/CONTRACT.md`** summarizing envelope, JWT header, MySQL, and `/api` prefix.

- [ ] **Step 8: Commit** (skip unless user asks)

---

### Task 3: ORM models + DB init + seed

**Files:**
- Create: `server/app/models/*.py`, `server/scripts/init_db.py`, `server/scripts/seed.py`
- Modify: `server/app/db/base.py` to import all models

**Interfaces:**
- Produces: tables `users`, `roles`, `permissions`, `user_roles`, `role_permissions`; function `seed_all(session)`; demo users as in spec

- [ ] **Step 1: Define association tables + models**

`role_permissions` and `user_roles` as SQLAlchemy `Table` objects; `User`, `Role`, `Permission` with relationships `roles`, `permissions`.

Permission seed list (exact codes):

```python
PERMISSIONS = [
    ("system", "role:read", "查看角色"),
    ("system", "role:write", "管理角色"),
    ("system", "user:read", "查看用户"),
    ("system", "user:assign_role", "分配角色"),
    ("ticket", "ticket:create", "创建工单"),
    ("ticket", "ticket:assign", "分派工单"),
    ("ticket", "ticket:handle", "处理工单"),
    ("ticket", "ticket:escalate", "升级工单"),
    ("ticket", "ticket:followup", "回访工单"),
    ("ticket", "ticket:close", "关闭工单"),
    ("ticket", "ticket:view_own", "查看自己的工单"),
    ("ticket", "ticket:view_all", "查看全部工单"),
    ("meta", "customer:manage", "管理客户"),
    ("meta", "category:manage", "管理分类"),
    ("meta", "priority:manage", "管理优先级"),
    ("meta", "rule:manage", "管理工单规则"),
]
```

Role defaults:
- `admin`: all codes
- `cs`: `role:read`, `user:read`, `ticket:create`, `ticket:assign`, `ticket:followup`, `ticket:close`, `ticket:view_all`
- `tech`: `ticket:handle`, `ticket:escalate`, `ticket:view_all`
- `customer`: `ticket:view_own`

- [ ] **Step 2: `init_db.py` creates database if missing then `Base.metadata.create_all`**

Use a root connection URL without DB name to `CREATE DATABASE IF NOT EXISTS ticket_support DEFAULT CHARSET utf8mb4`.

- [ ] **Step 3: `seed.py` upserts permissions/roles/users**

Hash passwords with `passlib.hash.bcrypt`. Idempotent: skip if username exists.

- [ ] **Step 4: Run against local MySQL**

```bash
cd server
copy .env.example .env
# edit MYSQL_PASSWORD
python -m scripts.init_db
python -m scripts.seed
```

Expected: no traceback; tables visible in MySQL.

- [ ] **Step 5: Commit** (skip unless user asks)

---

### Task 4: Security helpers + auth API (TDD)

**Files:**
- Create: `server/app/core/security.py`, `server/app/api/deps.py`, `server/app/schemas/auth.py`, `server/app/services/auth_service.py`, `server/app/api/auth.py`
- Modify: `server/app/main.py` include router
- Test: `server/tests/conftest.py`, `server/tests/test_auth.py`

**Interfaces:**
- Produces:
  - `create_access_token(user_id: int) -> str`
  - `verify_password(plain, hashed) -> bool`
  - `get_current_user(db, authorization) -> User`
  - `require_permissions(*codes)` dependency
  - `POST /api/auth/login` body `{username, password}`
  - `GET /api/auth/me` → `{id,username,displayName,roles,permissions,menus}`

- [ ] **Step 1: Write tests first**

`test_auth.py` (use TestClient + seeded SQLite override **or** MySQL test DB). Prefer conftest that creates tables on SQLite in-memory for unit speed:

```python
def test_login_ok(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "Admin@123"})
    assert res.json()["code"] == 200
    assert res.json()["data"]["token"]

def test_me_unauthorized(client):
    res = client.get("/api/auth/me")
    assert res.json()["code"] == 401
    assert res.json()["msg"] == "请先登录"

def test_login_wrong_password(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "bad"})
    assert res.json()["code"] in (400, 401)
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_auth.py -v
```

- [ ] **Step 3: Implement security + auth routes**

Parse Authorization:

```python
def extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return authorization.strip()
```

`/auth/me` menus (minimal ele-admin shape):

```python
MENUS = [
  {
    "path": "/system",
    "component": "/system",
    "meta": {"title": "系统管理", "icon": "SettingOutlined"},
    "children": [
      {"path": "/system/role", "component": "/system/role", "meta": {"title": "角色管理"}},
      {"path": "/system/user-role", "component": "/system/user-role", "meta": {"title": "用户赋权"}},
    ],
  }
]
```

Only include role menus if user has `role:read`; user-role if `user:read` or `user:assign_role`.

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit** (skip unless user asks)

---

### Task 5: Permissions + Roles API (TDD)

**Files:**
- Create: `server/app/api/permissions.py`, `server/app/api/roles.py`, `server/app/schemas/role.py`, `server/app/services/role_service.py`
- Test: `server/tests/test_roles.py`

**Interfaces:**
- `GET /api/permissions` → grouped `{module, items:[{id,code,name}]}`
- `GET /api/roles?page=1&pageSize=10` → `{records,total}`
- `GET/POST/PUT/DELETE /api/roles...` as spec

- [ ] **Step 1: Write tests**

```python
def _token(client, username="admin"):
    return client.post("/api/auth/login", json={"username": username, "password": "Admin@123"}).json()["data"]["token"]

def test_create_role_forbidden_for_customer(client):
    token = _token(client, "customer01")
    res = client.post("/api/roles", headers={"Authorization": token}, json={"code": "x", "name": "x", "permissionIds": []})
    body = res.json()
    assert body["code"] == 403
    assert "当前没有权限执行此操作" in body["msg"]

def test_cannot_delete_system_role(client):
    token = _token(client, "admin")
    # fetch admin role id then DELETE
    ...
    assert body["code"] == 400
```

- [ ] **Step 2: Run — FAIL; implement; Run — PASS**

Role list pagination field names: `records` + `total` (match `ele-pro-table` response mapping).

- [ ] **Step 3: Commit** (skip unless user asks)

---

### Task 6: Users list + assign roles API (TDD)

**Files:**
- Create: `server/app/api/users.py`, `server/app/schemas/user.py`, `server/app/services/user_service.py`
- Test: `server/tests/test_users.py`

**Interfaces:**
- `GET /api/users?page&pageSize&keyword` → `{records:[{id,username,displayName,roles:[{id,code,name}]}], total}`
- `PUT /api/users/{id}/roles` body `{roleIds: number[]}` requires `user:assign_role`

- [ ] **Step 1: Tests for list + assign + 403 for cs without assign if not granted**

(cs seed does **not** include `user:assign_role` — assert 403.)

- [ ] **Step 2: Implement + pass tests**

- [ ] **Step 3: Commit** (skip unless user asks)

---

### Task 7: Vite proxy → local FastAPI

**Files:**
- Modify: `.env.devLocal`, `vite.config.js`
- Create (optional): document in README snippet

**Interfaces:**
- Produces: with `VITE_TICKET_PROXY_TARGET=http://127.0.0.1:8000`, all `/api` requests in `devLocal` go to FastAPI (replace current catch-all target for local ticket work).

- [ ] **Step 1: Add to `.env.devLocal`**

```env
VITE_TICKET_PROXY_TARGET=http://127.0.0.1:8000
VITE_USE_TICKET_API=true
```

- [ ] **Step 2: Update `vite.config.js` proxy**

When `env.VITE_TICKET_PROXY_TARGET` is set, configure:

```js
'/api': {
  target: env.VITE_TICKET_PROXY_TARGET,
  changeOrigin: true,
  configure(proxy) {
    proxy.on('proxyReq', (proxyReq, req) => {
      console.log('[ticket-proxy]', req.method, req.url, '→', env.VITE_TICKET_PROXY_TARGET);
    });
  }
}
```

Place this **before** other `/api/...` specific proxies **or** gate the old `/api` catch-all behind `!VITE_TICKET_PROXY_TARGET` so ticket mode does not hit `test-portal`.

Keep `/api/sishu`, `/api/peiyou`, `/api/zhongkao` only when ticket proxy is **unset** (avoid breaking other modes). Simplest rule: if `VITE_TICKET_PROXY_TARGET` set, proxy object is **only** `{ '/api': { target: ticket } }`.

- [ ] **Step 3: Manual check**

```bash
# terminal A
cd server && uvicorn app.main:app --reload --port 8000
# terminal B
cd .. && npm run dev
curl http://127.0.0.1:90/api/health
```

Expected: JSON `code=200` and vite log `[ticket-proxy]`.

- [ ] **Step 4: Commit** (skip unless user asks)

---

### Task 8: Frontend auth wiring for ticket mode

**Files:**
- Create: `src/api/ticketAuth/index.js`, `src/config/ticket-menus.js`
- Modify: `src/api/login/index.js` (branch), `src/store/modules/user.js` (`fetchUserInfo`), `src/router/routes.js` (glob for `/src/views/system/**`)

**Interfaces:**
- When `import.meta.env.VITE_USE_TICKET_API === 'true'`:
  - login → `POST /auth/login` with `{username, password}` mapped from form `account`/`password`
  - user info → `GET /auth/me`
  - menus from `data.menus`

- [ ] **Step 1: API module**

```javascript
import request from '@/utils/request';

export async function ticketLogin(data) {
  const res = await request.post('/auth/login', data);
  if (res.data.code === 200) return res.data.data;
  return Promise.reject(new Error(res.data.msg || '登录失败'));
}

export async function ticketMe() {
  const res = await request.get('/auth/me');
  if (res.data.code === 200) return res.data.data;
  return Promise.reject(new Error(res.data.msg || '获取用户信息失败'));
}
```

Note: `baseURL` is `/api`, so path is `/auth/login` → `/api/auth/login`.

- [ ] **Step 2: Branch `login()` in `src/api/login/index.js`**

If ticket flag: call `ticketLogin({ username: data.account, password: data.password })`, `setToken(result.token, true)`, return msg.

- [ ] **Step 3: In `fetchUserInfo`, if ticket flag: call `ticketMe()`, `setInfo`, set `this.authorities = result.permissions`, `this.roles = result.roles`, return `{ menus: result.menus, homePath: '/system/role' }`.**

- [ ] **Step 4: Expand `import.meta.glob` in `routes.js`:**

```js
const modules = import.meta.glob([
  '/src/views/login/**/*.vue',
  '/src/views/welcome/**/*.vue',
  '/src/views/exception/**/*.vue',
  '/src/views/system/**/*.vue',
  '/src/views/base/**/*.vue',
  '/src/views/accountConfig/**/*.vue',
]);
```

- [ ] **Step 5: Manual login with `admin` / `Admin@123`** — expect enter layout with 系统管理 menu.

- [ ] **Step 6: Commit** (skip unless user asks)

---

### Task 9: Role management pages

**Files:**
- Create: `src/api/role/index.js`, `src/views/system/role/index.vue`, `src/views/system/role/components/role-edit-drawer.vue`
- Pattern reference: `src/views/base/classroomConfig/index.vue`

**Interfaces:**
- Consumes: `/roles`, `/roles/{id}`, `/permissions`, CRUD as Task 5
- Produces: list + drawer with checkbox group by module

- [ ] **Step 1: API**

```javascript
export async function pageRoles(params) {
  const res = await request.get('/roles', { params });
  if (res.data.code === 200) return res.data.data;
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}
// getRole, createRole, updateRole, deleteRole, listPermissions — same pattern
```

- [ ] **Step 2: List page** columns: name, code, isSystem, description, action (edit/delete). Hide delete for `isSystem`. Hide create/edit if authority lacks `role:write` (check `userStore.authorities`).

- [ ] **Step 3: Drawer** form: code (disable on edit), name, description, `el-checkbox-group` per module from `listPermissions()`.

- [ ] **Step 4: On API error with msg, `EleMessage.error(err.message)` — covers 403 Chinese text.

- [ ] **Step 5: Manual QA with admin vs customer01.

- [ ] **Step 6: Commit** (skip unless user asks)

---

### Task 10: User-role page + end-to-end smoke

**Files:**
- Create: `src/api/userRole/index.js`, `src/views/system/user-role/index.vue`, `src/views/system/user-role/components/assign-role-drawer.vue`

- [ ] **Step 1: Implement list + assign drawer (multi-select roles)**

- [ ] **Step 2: E2E smoke checklist**

1. Start MySQL, `python -m scripts.init_db && python -m scripts.seed`
2. `uvicorn app.main:app --reload --port 8000`
3. `npm run dev`
4. Login `admin` → open 角色管理 → create role `demo` → assign perms → save
5. Open 用户赋权 → set `cs01` roles include `demo` → logout → login `cs01` → `/auth/me` shows new perms
6. Login `customer01` → 角色管理 create → see `当前没有权限执行此操作`

- [ ] **Step 3: Mark OpenSpec `tasks.md` items done; run `openspec validate role-management`**

- [ ] **Step 4: Commit** (skip unless user asks)

---

## Spec coverage self-check

| Spec item | Task |
|-----------|------|
| OpenSpec change | 1 |
| FastAPI server under `server/` | 2–6 |
| MySQL `ticket_support` + seed | 3 |
| JWT login + `/me` | 4, 8 |
| RBAC APIs + 403 Chinese | 5–6 |
| Vite proxy | 7 |
| Role UI + user assign UI | 9–10 |
| Ticket APIs / SLA / customers | Out of scope (noted) |

## Placeholder scan

No TBD/TODO left in task steps; commit steps gated on user request.

## Type consistency

- Pagination: always `records` + `total`
- Permission codes: colon form `role:write`
- Login body backend: `username`/`password`; frontend maps from `account`
- Menu `component`: `/system/role` resolves to `src/views/system/role/index.vue` via glob
