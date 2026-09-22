# Proposal

## Why

Ticket support needs configurable RBAC before the ticket lifecycle so admin/cs/tech/customer capabilities are data-driven instead of hard-coded.

## What Changes

- Initialize OpenSpec workflow for this repo
- Add FastAPI + MySQL backend under `server/` with JWT login and RBAC APIs
- Add Vue role management and user-role assignment pages
- Point Vite `devLocal` `/api` proxy at the local FastAPI server
- Seed four system roles and demo users

## Capabilities

### New Capabilities

- `auth`: Password login issues JWT; current-user profile returns roles, permissions, and menus
- `rbac`: Role CRUD with permission binding; assign roles to users; system roles cannot be deleted

### Modified Capabilities

- (none — greenfield capabilities)

## Impact

- New `server/` Python service and MySQL database `ticket_support`
- Frontend login / user-info / menus branch when `VITE_USE_TICKET_API=true`
- `vite.config.js` and `.env.devLocal` proxy changes for local ticket mode
- Out of scope: ticket CRUD, SLA, customer management, remote uber usercenter
