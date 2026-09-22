# Ticket AI Agent P1 Design

**Date:** 2026-09-22  
**Status:** Approved for planning (pending user review of this file)  
**Scope:** P1 only — Agent core + independent chat UI. Deferred: RAG, Langfuse, human interrupt, close/delete tools, changes to existing ticket frontend.

## Context

The repo already has a deployed-style B-end ticket system:

- `server/` — FastAPI ticket backend (JWT + RBAC), port `:8000` locally
- Root `src/` — Vue ticket admin UI bound to that backend

P1 adds an AI agent that **calls existing ticket HTTP APIs** (does not open the ticket DB) for intelligent Q&A, ticket query, and adding notes. A separate Vue app hosts the chat UI so the existing ticket frontend remains untouched.

## Goals

1. Independent Agent service on `:8001` with LangGraph ReAct + OpenAI-compatible LLM.
2. Tools: `get_ticket_info` (read), `add_ticket_note` (low-risk write); JWT forwarded; RBAC enforced by ticket API.
3. SSE streaming chat API for clients.
4. New `agent-web/` (Vue + Vite + Element Plus) login + chat page; **zero changes** to root `src/` / root `vite.config.js`.
5. Extension points left for P2+ (interrupt, RAG, observability) without rewriting the service boundary.

## Non-goals (P1)

- RAG / PGVector / BM25 / Rerank
- Langfuse traces
- Golden test suite / badcase pipeline
- Human `interrupt` for high-risk writes
- `close_ticket` / `delete_ticket` tools (close API exists; whole-ticket delete does not)
- Modifying existing ticket frontend or its menus
- Jev / advanced intent router

## Architecture

```
agent-web (:91)
  ├── /api/*        → ticket server (:8000)   # login, /auth/me
  └── /agent-api/*  → agent (:8001)           # SSE chat

agent (:8001)
  ├── validate JWT via ticket GET /api/auth/me
  ├── LangGraph ReAct + MemorySaver(threadId)
  └── tools → HTTP → ticket /api/tickets...
        (Authorization header forwarded)
```

### Directory layout

```
ticket/
  server/          # existing; P1 does not change ticket business APIs for Agent
  src/             # existing ticket UI — P1 zero diff
  agent/           # NEW Agent API
    app/main.py
    app/api/chat.py
    app/graph/
    app/tools/
    app/clients/ticket_api.py
    requirements.txt
    .env.example
  agent-web/       # NEW AI chat UI (Vue + Vite + Element Plus)
  docs/superpowers/specs/...
```

### Trust and auth boundary

- Agent never trusts the model for authorization.
- Every tool call uses the **same user JWT** against ticket APIs.
- Agent may cache `/api/auth/me` summary in graph state for prompt context; permissions are still re-enforced by ticket endpoints.
- `auth_header` is runtime-only: not sent to the LLM as message content; logs may store token prefix/suffix only.

## API contract

### `GET /agent-api/health`

Liveness; no auth required.

### `POST /agent-api/chat`

- Headers: `Authorization: Bearer <ticket JWT>`
- Request JSON:

```json
{
  "threadId": "optional; omit to create",
  "message": "user text"
}
```

- Response: `text/event-stream`

| event | Purpose | `data` fields |
|-------|---------|----------------|
| `meta` | Session meta | `threadId` |
| `token` | Incremental assistant text | `content` |
| `tool_start` | Tool starting | `name`, `args` |
| `tool_end` | Tool finished | `name`, `ok`, `summary` |
| `error` | User-visible failure | `message` |
| `done` | Turn complete | `threadId` |

Auth failure before graph: HTTP **401** (not an SSE `error` event).

## Tools

### HTTP client

- Env: `TICKET_API_BASE` (default `http://127.0.0.1:8000`)
- Parse ticket envelope `{ code, data, msg }`; non-zero → tool error string for the model; emit `tool_end.ok=false` on SSE.

### `get_ticket_info` (read)

Maps to:

- `GET /api/tickets` (filters: keyword / ticketNo / status / page / pageSize)
- and/or `GET /api/tickets/{id}`

Rules:

- Prefer detail when `ticket_id` (or unambiguous ticket no) is known.
- Cap list results (e.g. 10 briefs) and trim detail fields to keep context small.
- No retries beyond one optional timeout retry.

### `add_ticket_note` (write, low risk)

Maps to `POST /api/tickets/{id}/notes` with `{ content, internal? }`.

Rules:

- Ticket side requires `ticket:handle` and handler (or existing `_can_record`) rules — Agent must surface 403/business errors honestly.
- **No automatic retry** on write.

### Explicitly not in P1

- `close_ticket` → `POST /api/tickets/{id}/close` (P2 + interrupt)
- `delete_ticket` — no whole-ticket delete API today; out of scope

## Graph and state

### Graph style

Single LangGraph **ReAct** agent (tool-calling loop). Soft intent via system prompt:

- Small talk → answer without tools
- Ticket facts → must call tools; never invent ticket data
- Notes → only via `add_ticket_note`

Leave a clear module boundary so P2 can insert a router / `interrupt` without changing the HTTP surface.

### State

- `messages` — chat history with add reducer
- `user` — `{ id, username, displayName, permissions[] }` from `/api/auth/me`
- `auth_header` — opaque runtime credential (not LLM-visible)

### Checkpointer

- P1: in-process `MemorySaver` keyed by `threadId`
- Restart loses threads; acceptable for P1
- `agent-web` may keep a local thread list in `localStorage`

### Limits

- `MAX_INPUT_CHARS` (e.g. 4000) — truncate with notice
- `MAX_TOOL_ROUNDS` (e.g. 6) — stop tool loop and conclude
- `TICKET_HTTP_TIMEOUT_SEC` — HTTP timeout to ticket API

## agent-web UI

- Stack: Vue 3 + Vite + Element Plus (same family as ticket UI, **separate app**)
- Pages: login (ticket `/api/auth/login`) + chat (`/` or `/chat`)
- Login password transport must match ticket backend: send `MD5(plain)` hex (same as existing ticket UI), not raw password
- Layout: left thread list (local), right streaming transcript + tool status chips
- Dev proxies:
  - `/api` → `http://127.0.0.1:8000`
  - `/agent-api` → `http://127.0.0.1:8001`
- Must not import or patch root `src/`

## Configuration

### `agent/.env`

| Variable | Role |
|----------|------|
| `TICKET_API_BASE` | Ticket server base URL |
| `OPENAI_API_BASE` | OpenAI-compatible base URL |
| `OPENAI_API_KEY` | API key |
| `OPENAI_MODEL` | Model name |
| `AGENT_HOST` / `AGENT_PORT` | Bind (default `8001`) |
| `MAX_INPUT_CHARS` | Input truncate |
| `MAX_TOOL_ROUNDS` | Tool loop cap |
| `TICKET_HTTP_TIMEOUT_SEC` | Ticket HTTP timeout |

### `agent-web`

- `VITE_API_URL=/api`
- `VITE_AGENT_API_URL=/agent-api`

## Error handling (P1)

| Case | Behavior |
|------|----------|
| Missing/invalid JWT | HTTP 401 |
| Ticket API timeout (read) | Optional 1 retry; then tool error |
| Ticket API failure (write note) | No retry; `tool_end.ok=false` |
| LLM / upstream failure | SSE `error`; thread remains usable |
| Tool round cap | Stop tools; answer with what is known or ask user to narrow |

## Acceptance criteria

1. `server`, `agent`, `agent-web` run locally together.
2. Login on `agent-web` with a ticket user; chat streams tokens over SSE.
3. Queries like “查工单 …” trigger `get_ticket_info`; data matches ticket API for that user.
4. “给工单加备注” succeeds only when ticket RBAC allows; otherwise clear failure (no fake success).
5. Root ticket frontend (`src/`, root Vite config) has **no P1 changes**.
6. Agent cannot close or delete tickets in P1 (tools not registered).

## Follow-on phases (out of this spec)

| Phase | Focus |
|-------|--------|
| P2 | High-risk tools + `interrupt` human confirm; retries/circuit patterns |
| P3 | RAG (PGVector hybrid retrieval), Langfuse, Golden tests |
| P4 | Optional embed into ticket UI or Nginx `/agent-api` / `/langfuse` production wiring |

## Decisions log

| Topic | Choice |
|-------|--------|
| Phase | P1 only |
| LLM | OpenAI-compatible (`base_url` + `api_key`) |
| Graph | Single ReAct (Approach A) |
| Streaming | SSE from day one |
| UI | New `agent-web/` in-repo; do not modify existing ticket `src/` |
| Chat UI shape | Dedicated chat page (not floating drawer) |
| Persistence | MemorySaver + client `threadId` |
| Auth | Forward ticket JWT; validate via `/api/auth/me` |
