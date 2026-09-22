## Purpose

Provides password login with JWT issuance and a current-user profile that exposes roles, permission codes, and menus for the admin UI.

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
