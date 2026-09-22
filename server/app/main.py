from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, customers, dicts, groups, rbac, tickets
from app.core.response import envelope, ok
from app.db.base import Base
from app.db.session import engine
from app.models import Customer, DictItem, DictType, Ticket, TicketAttachment, TicketCategory, TicketLog, TicketPriority  # noqa: F401

app = FastAPI(title="ticket-support")


@app.on_event("startup")
def ensure_tables():
    from sqlalchemy import inspect, text

    from app.db.session import SessionLocal
    from scripts.seed_data import (
        seed_demo_tickets,
        seed_dictionaries,
        seed_handler_groups,
        seed_ticket_meta,
    )

    inspector = inspect(engine)
    if "tickets" in set(inspector.get_table_names()):
        columns = {col["name"] for col in inspector.get_columns("tickets")}
        if "description" not in columns:
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS tickets"))
        elif "ticket_no" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE tickets "
                        "ADD COLUMN ticket_no VARCHAR(32) NOT NULL DEFAULT ''"
                    )
                )
        if "description" in columns and "group_role_id" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE tickets ADD COLUMN group_role_id INTEGER NULL")
                )
        if "description" in columns and "handler_group_id" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE tickets ADD COLUMN handler_group_id INTEGER NULL")
                )
        if "description" in columns and "sla_started_at" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN sla_started_at DATETIME NULL"))
        if "description" in columns and "sla_paused_seconds" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE tickets ADD COLUMN sla_paused_seconds INTEGER NOT NULL DEFAULT 0"
                    )
                )
        if "description" in columns and "sla_pause_started_at" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE tickets ADD COLUMN sla_pause_started_at DATETIME NULL")
                )
        if "description" in columns and "source" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE tickets ADD COLUMN source VARCHAR(16) NOT NULL DEFAULT 'staff'"
                    )
                )
        if "description" in columns and "handler_reply" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN handler_reply TEXT NULL"))
        if "description" in columns and "handler_solution" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN handler_solution TEXT NULL"))
        if "description" in columns and "rating" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE tickets ADD COLUMN rating INTEGER NOT NULL DEFAULT 0")
                )
        if "description" in columns and "followup_remark" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE tickets ADD COLUMN followup_remark TEXT NOT NULL DEFAULT ''")
                )
        if "description" in columns and "followup_method" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE tickets ADD COLUMN followup_method VARCHAR(16) NOT NULL DEFAULT ''"
                    )
                )
        if "description" in columns and "followup_at" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN followup_at DATETIME NULL"))
        if "description" in columns and "followup_user_id" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE tickets ADD COLUMN followup_user_id INTEGER NULL")
                )
    if "customers" in set(inspector.get_table_names()):
        customer_columns = {col["name"] for col in inspector.get_columns("customers")}
        if "user_id" not in customer_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE customers ADD COLUMN user_id INTEGER NULL"))
    if "handler_groups" in set(inspector.get_table_names()):
        group_columns = {col["name"] for col in inspector.get_columns("handler_groups")}
        if "leader_id" not in group_columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE handler_groups ADD COLUMN leader_id INTEGER NULL")
                )
    if "ticket_attachments" in set(inspector.get_table_names()):
        attachment_columns = {col["name"] for col in inspector.get_columns("ticket_attachments")}
        if "url" not in attachment_columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE ticket_attachments "
                        "ADD COLUMN url VARCHAR(512) NOT NULL DEFAULT ''"
                    )
                )
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_ticket_meta(db)
        seed_handler_groups(db)
        seed_dictionaries(db)
        seed_demo_tickets(db)
        from app.models import HandlerGroup, TicketLog
        from app.ticket_flow import build_ticket_no

        for row in db.query(Ticket).filter(Ticket.ticket_no == "").all():
            row.ticket_no = build_ticket_no(row.id, row.created_at)
        ask_ids = [
            row[0]
            for row in db.query(TicketLog.ticket_id)
            .filter(TicketLog.action == "ask")
            .distinct()
            .all()
        ]
        if ask_ids:
            db.query(Ticket).filter(Ticket.id.in_(ask_ids), Ticket.source != "ask").update(
                {Ticket.source: "ask"}, synchronize_session=False
            )
        for group in db.query(HandlerGroup).all():
            if group.name:
                db.query(Ticket).filter(
                    Ticket.group_name == group.name,
                    Ticket.handler_group_id.is_(None),
                ).update({Ticket.handler_group_id: group.id}, synchronize_session=False)
        db.commit()
    finally:
        db.close()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    code = exc.status_code
    msg = exc.detail if isinstance(exc.detail, str) else "请求失败"
    return JSONResponse(status_code=200, content=envelope(code, None, msg))


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.get("/api/health")
def health():
    return ok({"status": "up"})


app.include_router(auth.router)
app.include_router(rbac.router)
app.include_router(groups.router)
app.include_router(customers.router)
app.include_router(dicts.router)
app.include_router(tickets.router)

media_dir = Path(__file__).resolve().parents[1] / "uploads"
media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/media", StaticFiles(directory=media_dir), name="media")
