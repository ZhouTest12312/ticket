# Backend contract for ticket-support FastAPI service

## Stack

- FastAPI + SQLAlchemy 2 + MySQL (`ticket_support`)
- JWT auth via `Authorization` header (raw token or `Bearer <token>`)

## Response envelope

All business responses:

```json
{ "code": 200, "data": {}, "msg": "ok" }
```

- Success: `code === 200`
- Unauthorized: `code === 401`, `msg` = `请先登录`
- Forbidden: `code === 403`, `msg` contains `当前没有权限执行此操作`
- HTTP status is typically 200; clients must read `code`

## Prefix

All routes under `/api`.
