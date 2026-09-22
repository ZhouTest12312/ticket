# ticket-support server

## Setup

```bash
cd server
py -3.13 -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
copy .env.example .env
# edit .env: USE_SQLITE=true 或填 MYSQL_PASSWORD 且 USE_SQLITE=false
.\.venv\Scripts\python.exe -m scripts.init_db
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Seed users (initial password `Admin@123`): admin / cs01 / tech01 / customer01

`scripts.seed` / `init_db` only set the password when creating a user; they do **not** overwrite an existing `password_hash` (so change-password survives re-seed). To force-reset demo passwords, update rows manually or delete users then re-seed.

Password transport: frontend sends `CryptoJS.MD5(plain).toString()`; server stores `bcrypt(md5)`.

## Tests

```bash
.\.venv\Scripts\python.exe -m pytest tests -v
```
