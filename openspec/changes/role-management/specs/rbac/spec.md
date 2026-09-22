## Purpose

Provides role and permission administration so operators can configure RBAC bindings and assign roles to users without code changes.

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

#### Scenario: Assign roles succeeds for admin
- **WHEN** an admin PUTs role ids for a user
- **THEN** response `code` is 200 and subsequent `/api/auth/me` for that user reflects the new roles
