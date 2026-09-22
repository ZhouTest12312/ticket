# Design: role-management

Canonical design: `docs/superpowers/specs/2026-09-20-role-management-design.md`

## Summary

- Backend: `server/` FastAPI + SQLAlchemy + MySQL (`ticket_support`)
- Auth: self-issued JWT in `Authorization` (raw or `Bearer`)
- RBAC: users ↔ roles ↔ permissions
- Envelope: `{ code, data, msg }`; HTTP often 200 with business `code`
- 403 msg: `当前没有权限执行此操作`; 401 msg: `请先登录`
- Frontend: role list/edit + user assign; `devLocal` proxies `/api` → `:8000`

## API (Phase 1)

| Method | Path | Permission |
|--------|------|------------|
| POST | `/api/auth/login` | public |
| GET | `/api/auth/me` | login |
| GET | `/api/permissions` | `role:read` |
| GET/POST/PUT/DELETE | `/api/roles` | `role:read` / `role:write` |
| GET | `/api/users` | `user:read` |
| PUT | `/api/users/{id}/roles` | `user:assign_role` |

## Decisions

- System roles `admin`/`cs`/`tech`/`customer`: editable perms, not deletable
- Seed password `Admin@123` for demo accounts
- Ticket permission codes pre-seeded; ticket APIs deferred
