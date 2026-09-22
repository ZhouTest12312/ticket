from datetime import datetime, timedelta
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permissions, user_permission_codes
from app.core.response import fail_response, ok
from app.db.session import get_db
from app.models import (
    Customer,
    HandlerGroup,
    Role,
    Ticket,
    TicketAttachment,
    TicketCategory,
    TicketCollaborator,
    TicketFormerAssignee,
    TicketLog,
    TicketPriority,
    User,
    DictItem,
    DictType,
)
from app.ticket_flow import (
    ACTION_LABEL,
    FOLLOWUP_METHODS,
    FOLLOWUP_RESULTS,
    HANDLER_PENDING,
    STATUS_LABEL,
    AUTO_CLOSE_HOURS,
    build_ticket_no,
    fmt_dt,
    parse_dt,
    sla_info,
)

router = APIRouter(prefix="/api", tags=["tickets"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
MAX_SIZE = 50 * 1024 * 1024
KINDS = {"screenshot", "log", "file", "solution", "image", "video"}


def _name(user: User | None) -> str:
    if not user:
        return ""
    return user.display_name or user.username


def _from_customer(user: User | None) -> bool:
    if not user:
        return False
    codes = {role.code for role in user.roles}
    return "customer" in codes and codes.isdisjoint({"admin", "tech", "cs"})


def _add_log(db: Session, ticket: Ticket, user: User | None, action: str, content: str) -> None:
    db.add(
        TicketLog(
            ticket_id=ticket.id,
            action=action,
            content=content,
            operator_id=user.id if user else None,
        )
    )


def _is_admin(user: User) -> bool:
    return any(role.code == "admin" for role in user.roles)


def _is_staff(user: User) -> bool:
    return any(role.code != "customer" for role in user.roles)


def _flow_status(ticket: Ticket) -> str:
    return "processing" if ticket.status == "overdue" else ticket.status


def _user_group_names(user: User) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for role in user.roles:
        if role.code == "customer":
            continue
        for group in role.handler_groups:
            if group.name in seen:
                continue
            seen.add(group.name)
            names.append(group.name)
    return names


def _user_handler_group(user: User) -> HandlerGroup | None:
    for role in user.roles:
        if role.code in {"customer", "admin"}:
            continue
        if role.handler_groups:
            return role.handler_groups[0]
    return None


def _handler_role(user: User) -> Role | None:
    by_code = {role.code: role for role in user.roles}
    for code in ("tech", "cs", "admin"):
        if code in by_code:
            return by_code[code]
    for role in user.roles:
        if role.code != "customer":
            return role
    return None


def _can_edit_base(user: User, ticket: Ticket) -> bool:
    if ticket.status != "unassigned":
        return False
    if _is_admin(user):
        return True
    return ticket.creator_id == user.id or _is_ticket_customer(user, ticket)


def _can_change_status(user: User, ticket: Ticket) -> bool:
    if _is_admin(user):
        return True
    return ticket.assignee_id == user.id


def _is_group_leader(user: User, ticket: Ticket) -> bool:
    group = ticket.handler_group
    return bool(group and group.leader_id == user.id)


def _is_collaborator(user: User, ticket: Ticket) -> bool:
    return any(u.id == user.id for u in ticket.collaborators)


def _can_record(user: User, ticket: Ticket) -> bool:
    return _can_change_status(user, ticket)


def _led_group_ids(db: Session, user: User) -> list[int]:
    return [
        row[0]
        for row in db.query(HandlerGroup.id).filter(HandlerGroup.leader_id == user.id).all()
    ]


def _is_any_group_leader(db: Session, user: User) -> bool:
    return bool(_led_group_ids(db, user))


def _apply_rating(ticket: Ticket, body: dict) -> str | None:
    raw = body.get("rating")
    if raw in (None, ""):
        return None
    try:
        rating = int(raw)
    except (TypeError, ValueError):
        return "评分格式不正确"
    if rating < 1 or rating > 5:
        return "请选择 1-5 星评价"
    ticket.rating = rating
    return None


def _customer_account(db: Session, user: User) -> Customer | None:
    return db.query(Customer).filter(Customer.user_id == user.id).first()


def _is_ticket_customer(user: User, ticket: Ticket) -> bool:
    return bool(ticket.customer and ticket.customer.user_id == user.id)


def _is_former_assignee(db: Session, user: User, ticket: Ticket) -> bool:
    return (
        db.query(TicketFormerAssignee)
        .filter(
            TicketFormerAssignee.ticket_id == ticket.id,
            TicketFormerAssignee.user_id == user.id,
        )
        .first()
        is not None
    )


def _remember_former_assignee(db: Session, ticket: Ticket, user_id: int | None) -> None:
    if not user_id or user_id == ticket.assignee_id:
        return
    exists = (
        db.query(TicketFormerAssignee)
        .filter(
            TicketFormerAssignee.ticket_id == ticket.id,
            TicketFormerAssignee.user_id == user_id,
        )
        .first()
    )
    if not exists:
        db.add(TicketFormerAssignee(ticket_id=ticket.id, user_id=user_id))


def _can_view(db: Session, user: User, ticket: Ticket) -> bool:
    if _is_admin(user) or "ticket:view_all" in user_permission_codes(user):
        return True
    if ticket.creator_id == user.id or _is_ticket_customer(user, ticket):
        return True
    if ticket.status == "closed" and "ticket:followup" in user_permission_codes(user):
        return True
    if ticket.status == "unassigned":
        return False
    return (
        ticket.assignee_id == user.id
        or _is_collaborator(user, ticket)
        or _is_former_assignee(db, user, ticket)
    )


def _restrict_visible(q, db: Session, user: User):
    if _is_admin(user) or "ticket:view_all" in user_permission_codes(user):
        return q
    codes = user_permission_codes(user)
    collab_ids = [
        row[0]
        for row in db.query(TicketCollaborator.ticket_id)
        .filter(TicketCollaborator.user_id == user.id)
        .all()
    ]
    former_ids = [
        row[0]
        for row in db.query(TicketFormerAssignee.ticket_id)
        .filter(TicketFormerAssignee.user_id == user.id)
        .all()
    ]
    conds = [Ticket.assignee_id == user.id]
    if collab_ids:
        conds.append(Ticket.id.in_(collab_ids))
    if former_ids:
        conds.append(Ticket.id.in_(former_ids))
    if "ticket:followup" in codes:
        conds.append(Ticket.status == "closed")
    return q.filter(or_(*conds), Ticket.status != "unassigned")


def _can_list_tickets(db: Session, user: User) -> bool:
    codes = user_permission_codes(user)
    if codes.intersection(
        {
            "ticket:view_all",
            "ticket:view_own",
            "ticket:ask",
            "ticket:handle",
            "ticket:create",
            "ticket:assign",
        }
    ):
        return True
    if (
        db.query(TicketCollaborator.ticket_id)
        .filter(TicketCollaborator.user_id == user.id)
        .first()
        is not None
    ):
        return True
    return _is_any_group_leader(db, user)


def _has_customer_feedback(ticket: Ticket) -> bool:
    for log in ticket.logs or []:
        if log.action != "record" or not log.operator:
            continue
        if any(role.code == "customer" for role in log.operator.roles):
            return True
    return False


def _ticket_brief(ticket: Ticket) -> dict:
    sla = sla_info(ticket)
    return {
        "id": ticket.id,
        "ticketNo": ticket.ticket_no or build_ticket_no(ticket.id, ticket.created_at),
        "title": ticket.title,
        "customerId": ticket.customer_id,
        "customerName": ticket.customer.name if ticket.customer else "",
        "customerUserId": ticket.customer.user_id if ticket.customer else None,
        "categoryName": ticket.category.name if ticket.category else "",
        "priorityName": ticket.priority.name if ticket.priority else "",
        "priorityId": ticket.priority_id,
        "status": ticket.status,
        "statusLabel": STATUS_LABEL.get(ticket.status, ticket.status),
        "assigneeId": ticket.assignee_id,
        "assigneeName": _name(ticket.assignee),
        "creatorName": _name(ticket.creator),
        "groupName": ticket.group_name,
        "groupId": ticket.handler_group_id,
        "groupLeaderId": ticket.handler_group.leader_id if ticket.handler_group else None,
        "statusChangedAt": fmt_dt(ticket.status_changed_at),
        "createdAt": fmt_dt(ticket.created_at),
        "updatedAt": fmt_dt(ticket.updated_at),
        "collaboratorIds": [u.id for u in ticket.collaborators],
        "collaboratorNames": "、".join(
            _name(u) for u in ticket.collaborators if _name(u)
        ),
        "source": ticket.source or "staff",
        "sourceLabel": "客户提问" if ticket.source == "ask" else "后台创建",
        "rating": int(getattr(ticket, "rating", 0) or 0),
        "followedUp": bool(ticket.followup_at or (ticket.followup_result or "").strip()),
        "followupResult": ticket.followup_result or "",
        "expectedFinishAt": fmt_dt(ticket.expected_finish_at),
        "pendingConfirm": bool(ticket.pending_confirm),
        "handled": bool((ticket.handler_reply or "").strip()) or _has_customer_feedback(ticket),
        **sla,
    }


def _ticket_detail(ticket: Ticket) -> dict:
    data = _ticket_brief(ticket)
    data.update(
        {
            "description": ticket.description,
            "categoryId": ticket.category_id,
            "product": ticket.product,
            "orderNo": ticket.order_no,
            "serviceName": ticket.service_name,
            "estimatedResolveAt": fmt_dt(ticket.estimated_resolve_at),
            "actualResolveAt": fmt_dt(ticket.actual_resolve_at),
            "resolution": ticket.resolution,
            "handlerReply": ticket.handler_reply or "",
            "handlerSolution": ticket.handler_solution or "",
            "evaluation": ticket.evaluation,
            "rating": int(ticket.rating or 0),
            "followupResult": ticket.followup_result or "",
            "followupRemark": getattr(ticket, "followup_remark", "") or "",
            "followupMethod": getattr(ticket, "followup_method", "") or "",
            "followupAt": fmt_dt(getattr(ticket, "followup_at", None)),
            "followupUserId": getattr(ticket, "followup_user_id", None),
            "followupUserName": _name(getattr(ticket, "followup_user", None)),
            "followedUp": bool(
                getattr(ticket, "followup_at", None) or (ticket.followup_result or "").strip()
            ),
            "creatorName": _name(ticket.creator),
            "collaborators": [
                {"id": u.id, "name": _name(u)} for u in ticket.collaborators
            ],
            "logs": [
                {
                    "id": log.id,
                    "action": log.action,
                    "actionLabel": ACTION_LABEL.get(log.action, log.action),
                    "content": log.content,
                    "operatorName": _name(log.operator),
                    "operatorId": log.operator_id,
                    "fromCustomer": _from_customer(log.operator),
                    "operatorRoles": [role.name for role in log.operator.roles] if log.operator else [],
                    "createdAt": fmt_dt(log.created_at),
                }
                for log in sorted(ticket.logs, key=lambda item: item.id)
            ],
            "attachments": [
                {
                    "id": item.id,
                    "kind": item.kind,
                    "filename": item.filename,
                    "url": item.url or "",
                    "size": item.size,
                    "createdAt": fmt_dt(item.created_at),
                    "uploaderId": item.uploader_id,
                    "uploaderName": _name(item.uploader),
                    "fromCustomer": _from_customer(item.uploader),
                }
                for item in sorted(ticket.attachments, key=lambda item: item.id)
            ],
        }
    )
    return data


def _get_ticket(db: Session, ticket_id: int, user: User):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        return None, fail_response(404, "工单不存在")
    if not _can_view(db, user, ticket):
        return None, fail_response(403, "当前没有权限执行此操作")
    return ticket, None


def _set_status(ticket: Ticket, status: str) -> None:
    now = datetime.utcnow()
    if (
        ticket.status == "waiting_customer"
        and status != "waiting_customer"
        and ticket.sla_pause_started_at
    ):
        paused = int((now - ticket.sla_pause_started_at).total_seconds())
        ticket.sla_paused_seconds = (ticket.sla_paused_seconds or 0) + max(paused, 0)
        ticket.sla_pause_started_at = None
    if status == "waiting_customer" and ticket.status != "waiting_customer":
        ticket.sla_pause_started_at = now
    ticket.status = status
    ticket.status_changed_at = now
    ticket.updated_at = now


def _restart_staff_sla(ticket: Ticket, started_at: datetime | None = None) -> None:
    ticket.sla_started_at = started_at or datetime.utcnow()
    ticket.sla_paused_seconds = 0
    ticket.sla_pause_started_at = None


def _last_customer_reply_at(ticket: Ticket) -> datetime | None:
    logs = sorted(ticket.logs or [], key=lambda item: item.id)
    if not logs:
        return None
    latest = logs[-1]
    if latest.action not in {"record", "attachment"} or not latest.operator:
        return None
    if not any(role.code == "customer" for role in latest.operator.roles):
        return None
    return latest.created_at


def _recover_overdue_ticket(ticket: Ticket) -> bool:
    if ticket.status != "overdue":
        return False
    replied_at = _last_customer_reply_at(ticket)
    if replied_at:
        _restart_staff_sla(ticket, replied_at)
    _set_status(ticket, "processing")
    return True


def _sync_overdue(db: Session, tickets: list[Ticket]) -> bool:
    changed = False
    for ticket in tickets:
        if _recover_overdue_ticket(ticket):
            changed = True
    if changed:
        db.commit()
    return changed


def _admin_user(db: Session) -> User | None:
    return (
        db.query(User)
        .join(User.roles)
        .filter(Role.code == "admin", User.status == 1)
        .order_by(User.id.asc())
        .first()
    )


def _resolve_escalate_target(db: Session, ticket: Ticket) -> User | None:
    group = ticket.handler_group
    admin = _admin_user(db)
    default_target = None
    if group and group.leader_id and group.leader and group.leader.status == 1:
        default_target = group.leader
    if default_target and default_target.id == ticket.assignee_id:
        default_target = admin
    if not default_target:
        default_target = admin
    return default_target


def _perform_escalate(
    db: Session,
    ticket: Ticket,
    target: User,
    operator: User | None,
    reason: str,
) -> None:
    leader_group = (
        db.query(HandlerGroup).filter(HandlerGroup.leader_id == target.id).first()
    )
    if leader_group:
        ticket.handler_group_id = leader_group.id
        ticket.group_name = leader_group.name
    else:
        handler_role = _handler_role(target)
        if handler_role and handler_role.handler_groups:
            ticket.handler_group_id = handler_role.handler_groups[0].id
            ticket.group_name = handler_role.handler_groups[0].name
            ticket.group_role_id = handler_role.id
    previous_id = ticket.assignee_id
    ticket.assignee_id = target.id
    _remember_former_assignee(db, ticket, previous_id)
    urgent = db.query(TicketPriority).filter(TicketPriority.name == "紧急").first()
    if urgent:
        ticket.priority_id = urgent.id
    ticket.sla_started_at = datetime.utcnow()
    _set_status(ticket, "processing")
    _add_log(
        db,
        ticket,
        operator,
        "escalate",
        f"{reason}；升级后处理人：{_name(target)}，处理组：{ticket.group_name or '未指定'}，状态改为处理中，优先级改为紧急",
    )


def _apply_escalate(
    db: Session,
    ticket: Ticket,
    *,
    operator: User | None,
    reason: str = "处理超时，系统自动升级给负责人",
    target: User | None = None,
    require_new_assignee: bool = True,
) -> bool:
    if ticket.status in {"resolved", "closed", "ended", "unassigned"}:
        return False
    if ticket.status == "waiting_customer":
        return False
    if sla_info(ticket)["slaState"] != "overdue":
        return False
    target = target or _resolve_escalate_target(db, ticket)
    if not target:
        return False
    if require_new_assignee and target.id == ticket.assignee_id:
        return False
    _perform_escalate(db, ticket, target, operator, reason)
    return True


def _sync_sla(db: Session, tickets: list[Ticket]) -> bool:
    changed = False
    for ticket in tickets:
        if _recover_overdue_ticket(ticket):
            changed = True
        if _apply_escalate(db, ticket, operator=None):
            changed = True
    if changed:
        db.commit()
    return changed


SLA_SYNC_STATUSES = ("pending", "processing", "overdue", "reopened", "waiting_customer")


def _open_tickets_for_sla_sync(db: Session, user: User) -> list[Ticket]:
    q = db.query(Ticket).filter(Ticket.status.in_(SLA_SYNC_STATUSES))
    if _is_admin(user) or "ticket:view_all" in user_permission_codes(user):
        return q.all()
    return _restrict_visible(q, db, user).all()


def _enabled_dict_names(db: Session, type_code: str) -> set[str]:
    dtype = db.query(DictType).filter(DictType.code == type_code).first()
    if not dtype:
        return set()
    rows = (
        db.query(DictItem)
        .filter(DictItem.type_id == dtype.id, DictItem.status == 1)
        .all()
    )
    return {row.name for row in rows}


def _dict_choices(db: Session, type_code: str) -> list[dict]:
    dtype = db.query(DictType).filter(DictType.code == type_code).first()
    if not dtype:
        return []
    rows = (
        db.query(DictItem)
        .filter(DictItem.type_id == dtype.id, DictItem.status == 1)
        .order_by(DictItem.sort.asc(), DictItem.id.asc())
        .all()
    )
    return [{"id": row.id, "name": row.name} for row in rows]


def _check_dict_value(db: Session, type_code: str, value: str, previous: str = "") -> str | None:
    text = (value or "").strip()
    if not text or text == (previous or "").strip():
        return None
    label = "产品" if type_code == "product" else "具体服务"
    if text not in _enabled_dict_names(db, type_code):
        return f"请选择有效的{label}"
    return None


@router.get("/tickets/options")
def ticket_options(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    codes = user_permission_codes(user)
    if not codes.intersection(
        {
            "ticket:view_all",
            "ticket:view_own",
            "ticket:create",
            "ticket:handle",
            "ticket:assign",
            "ticket:ask",
        }
    ):
        return fail_response(403, "当前没有权限执行此操作")
    categories = db.query(TicketCategory).order_by(TicketCategory.sort, TicketCategory.id).all()
    priorities = db.query(TicketPriority).order_by(TicketPriority.level).all()
    customers = (
        db.query(Customer)
        .filter(Customer.status == 1, Customer.user_id.isnot(None))
        .order_by(Customer.id.desc())
        .limit(200)
        .all()
    )
    users = db.query(User).filter(User.status == 1).order_by(User.id.asc()).all()
    return ok(
        {
            "categories": [{"id": c.id, "name": c.name} for c in categories],
            "priorities": [
                {
                    "id": p.id,
                    "name": p.name,
                    "slaHours": p.sla_hours,
                    "warnHours": p.warn_hours,
                }
                for p in priorities
            ],
            "customers": [
                {
                    "id": c.id,
                    "name": c.name,
                    "userId": c.user_id,
                    "accountName": _name(c.user) if c.user else "",
                    "label": f"{c.name}（{_name(c.user)}）" if c.user else c.name,
                }
                for c in customers
            ],
            "products": _dict_choices(db, "product"),
            "services": _dict_choices(db, "service"),
            "users": [
                {
                    "id": u.id,
                    "name": _name(u),
                    "roleIds": [role.id for role in u.roles if role.code != "customer"],
                    "roleCodes": [role.code for role in u.roles],
                    "staff": _is_staff(u),
                    "groupNames": _user_group_names(u),
                }
                for u in users
            ],
            "technicians": [
                {"id": u.id, "name": _name(u)}
                for u in users
                if any(role.code == "tech" for role in u.roles)
            ],
            "escalationTargets": _escalation_targets(db),
            "groups": [
                {
                    "id": group.id,
                    "name": group.name,
                    "roleIds": [role.id for role in group.roles],
                    "leaderId": group.leader_id,
                    "leaderName": _name(group.leader) if group.leader else "",
                }
                for group in db.query(HandlerGroup).order_by(HandlerGroup.id.asc()).all()
            ],
            "statuses": [{"value": k, "label": v} for k, v in STATUS_LABEL.items()],
        }
    )


@router.get("/tickets/workload")
def ticket_workload(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("ticket:view_all")),
):
    rows = (
        db.query(Ticket)
        .filter(Ticket.assignee_id.isnot(None), Ticket.status.in_(HANDLER_PENDING))
        .all()
    )
    bucket: dict[int, dict] = {}
    for ticket in rows:
        item = bucket.setdefault(
            ticket.assignee_id,
            {"userId": ticket.assignee_id, "name": _name(ticket.assignee), "pendingCount": 0},
        )
        item["pendingCount"] += 1
    records = sorted(bucket.values(), key=lambda x: (-x["pendingCount"], x["userId"]))
    return ok(records)


@router.get("/tickets")
def list_tickets(
    page: int = 1,
    pageSize: int = 10,
    keyword: str = "",
    ticketNo: str = "",
    status: str = "",
    priorityId: int | None = None,
    assigneeId: int | None = None,
    overdue: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _can_list_tickets(db, user):
        return fail_response(403, "当前没有权限执行此操作")
    q = _restrict_visible(db.query(Ticket), db, user)
    if keyword.strip():
        like = f"%{keyword.strip()}%"
        q = q.filter(or_(Ticket.title.like(like), Ticket.description.like(like), Ticket.ticket_no.like(like)))
    if ticketNo.strip():
        number = ticketNo.strip()
        number_conds = [Ticket.ticket_no.like(f"%{number}%")]
        if number.isdigit():
            number_conds.append(Ticket.id == int(number))
        q = q.filter(or_(*number_conds))
    if priorityId is not None:
        q = q.filter(Ticket.priority_id == priorityId)
    if assigneeId is not None:
        q = q.filter(Ticket.assignee_id == assigneeId)
    items = q.order_by(Ticket.id.desc()).all()
    _sync_sla(db, items)
    if status:
        items = [ticket for ticket in items if ticket.status == status]
    if overdue == 1:
        items = [t for t in items if sla_info(t)["slaState"] == "overdue"]
    elif overdue == 2:
        items = [t for t in items if sla_info(t)["slaState"] == "warning"]
    total = len(items)
    start = max(page - 1, 0) * pageSize
    page_items = items[start : start + pageSize]
    return ok({"records": [_ticket_brief(t) for t in page_items], "total": total})


def _is_tech_leader(db: Session, user: User) -> bool:
    return (
        db.query(HandlerGroup.id)
        .filter(HandlerGroup.name == "技术组", HandlerGroup.leader_id == user.id)
        .first()
        is not None
    )


@router.get("/tickets/pending-count")
def pending_count(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
    _sync_sla(db, _open_tickets_for_sla_sync(db, user))
    if _is_admin(user):
        count = (
            db.query(Ticket)
            .filter(Ticket.status.in_(["unassigned", "pending"]))
            .count()
        )
        return ok({"count": count, "myOverdueCount": my_overdue})
    if not _can_list_tickets(db, user):
        return ok({"count": 0, "myOverdueCount": my_overdue})
    q = _restrict_visible(db.query(Ticket).filter(Ticket.status == "pending"), db, user)
    return ok({"count": q.count(), "myOverdueCount": my_overdue})


@router.get("/tickets/mine")
def list_my_tickets(
    page: int = 1,
    pageSize: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    codes = user_permission_codes(user)
    if "ticket:ask" not in codes and "ticket:view_own" not in codes and not _is_admin(user):
        return fail_response(403, "当前没有权限执行此操作")
    if _is_admin(user):
        q = db.query(Ticket).filter(Ticket.source == "ask")
        total = q.count()
        items = (
            q.order_by(Ticket.id.desc())
            .offset(max(page - 1, 0) * pageSize)
            .limit(pageSize)
            .all()
        )
        return ok({"records": [_ticket_brief(ticket) for ticket in items], "total": total})
    bound = _customer_account(db, user)
    if bound:
        q = db.query(Ticket).filter(
            (Ticket.creator_id == user.id) | (Ticket.customer_id == bound.id)
        )
    else:
        q = db.query(Ticket).filter(Ticket.creator_id == user.id)
    total = q.count()
    items = (
        q.order_by(Ticket.id.desc())
        .offset(max(page - 1, 0) * pageSize)
        .limit(pageSize)
        .all()
    )
    return ok({"records": [_ticket_brief(ticket) for ticket in items], "total": total})


@router.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    _sync_sla(db, [ticket])
    data = _ticket_detail(ticket)
    if _is_ticket_customer(user, ticket) and not _is_admin(user):
        data["logs"] = [
            item
            for item in data["logs"]
            if item["action"] not in {"internal", "followup"}
        ]
        for key in (
            "followupResult",
            "followupRemark",
            "followupMethod",
            "followupAt",
            "followupUserId",
            "followupUserName",
            "followedUp",
        ):
            data.pop(key, None)
    return ok(data)


@router.post("/tickets")
def create_ticket(
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("ticket:create")),
):
    title = str(body.get("title") or "").strip()
    description = str(body.get("description") or "").strip()
    if not title:
        return fail_response(400, "请输入问题标题")
    if not description:
        return fail_response(400, "请输入详细描述")
    if not body.get("categoryId"):
        return fail_response(400, "请选择问题分类")
    if not body.get("priorityId"):
        return fail_response(400, "请选择优先级")
    if not body.get("customerId"):
        return fail_response(400, "请关联客户")
    customer = db.get(Customer, int(body["customerId"]))
    if not customer:
        return fail_response(400, "客户不存在")
    if not customer.user_id:
        return fail_response(400, "请选择已绑定登录账号的客户")
    category = db.get(TicketCategory, int(body["categoryId"]))
    priority = db.get(TicketPriority, int(body["priorityId"]))
    if not category or not priority:
        return fail_response(400, "分类或优先级不存在")
    product = str(body.get("product") or "").strip()[:128]
    service_name = str(body.get("serviceName") or "").strip()[:128]
    order_no = str(body.get("orderNo") or "").strip()[:64]
    if not product:
        return fail_response(400, "请选择产品")
    if not order_no:
        return fail_response(400, "请输入订单号")
    if not service_name:
        return fail_response(400, "请选择具体服务")
    product_err = _check_dict_value(db, "product", product)
    if product_err:
        return fail_response(400, product_err)
    service_err = _check_dict_value(db, "service", service_name)
    if service_err:
        return fail_response(400, service_err)
    now = datetime.utcnow()
    ticket = Ticket(
        title=title[:200],
        description=description,
        category_id=category.id,
        priority_id=priority.id,
        customer_id=customer.id,
        product=product,
        order_no=order_no,
        service_name=service_name,
        expected_finish_at=parse_dt(body.get("expectedFinishAt")),
        estimated_resolve_at=parse_dt(body.get("estimatedResolveAt")),
        status="unassigned",
        status_changed_at=now,
        creator_id=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    db.flush()
    ticket.ticket_no = build_ticket_no(ticket.id, ticket.created_at)
    _add_log(db, ticket, user, "create", f"创建工单「{ticket.title}」")
    db.commit()
    db.refresh(ticket)
    return ok({"id": ticket.id}, msg="创建成功")


def _save_ask_attachments(db: Session, ticket: Ticket, user: User, raw):
    items = raw or []
    if not isinstance(items, list):
        return fail_response(400, "附件格式不正确")
    for item in items:
        if not isinstance(item, dict):
            return fail_response(400, "附件格式不正确")
        kind = str(item.get("kind") or "")
        url = str(item.get("url") or "").strip()
        filename = str(item.get("filename") or "附件").strip()[:255]
        if kind not in {"image", "video"}:
            return fail_response(400, "请上传图片或视频")
        if not (url.startswith("http") or url.startswith("/api/media/")):
            return fail_response(400, "附件地址无效")
        db.add(
            TicketAttachment(
                ticket_id=ticket.id,
                kind=kind,
                filename=filename or "附件",
                url=url[:512],
                stored_name="",
                size=0,
                uploader_id=user.id,
            )
        )
        kind_label = "图片" if kind == "image" else "视频"
        _add_log(db, ticket, user, "attachment", f"上传{kind_label}：{filename or '附件'}")
    return None


@router.post("/tickets/ask")
def ask_ticket(
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("ticket:ask")),
):
    customer = _customer_account(db, user)
    if not customer:
        return fail_response(400, "请管理员在「客户管理」中把本账号绑定到客户资料")
    title = str(body.get("title") or "").strip()
    description = str(body.get("description") or "").strip()
    if not title:
        return fail_response(400, "请输入问题标题")
    if not description:
        return fail_response(400, "请输入详细描述")
    if not body.get("categoryId"):
        return fail_response(400, "请选择分类")
    if not body.get("priorityId"):
        return fail_response(400, "请选择优先级")
    category = db.get(TicketCategory, int(body["categoryId"]))
    priority = db.get(TicketPriority, int(body["priorityId"]))
    if not category or not priority:
        return fail_response(400, "分类或优先级不存在")
    product = str(body.get("product") or "").strip()[:128]
    service_name = str(body.get("serviceName") or "").strip()[:128]
    if not product:
        return fail_response(400, "请选择产品")
    if not service_name:
        return fail_response(400, "请选择具体服务")
    product_err = _check_dict_value(db, "product", product)
    if product_err:
        return fail_response(400, product_err)
    service_err = _check_dict_value(db, "service", service_name)
    if service_err:
        return fail_response(400, service_err)
    now = datetime.utcnow()
    ticket = Ticket(
        title=title[:200],
        description=description,
        category_id=category.id,
        priority_id=priority.id,
        customer_id=customer.id,
        product=product,
        order_no=f"ASK-{now.strftime('%Y%m%d%H%M%S')}{user.id:04d}",
        service_name=service_name,
        status="unassigned",
        source="ask",
        status_changed_at=now,
        creator_id=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    db.flush()
    ticket.ticket_no = build_ticket_no(ticket.id, ticket.created_at)
    _add_log(db, ticket, user, "ask", f"客户提问「{ticket.title}」")
    attach_err = _save_ask_attachments(db, ticket, user, body.get("attachments"))
    if attach_err:
        db.rollback()
        return attach_err
    db.commit()
    db.refresh(ticket)
    return ok({"id": ticket.id}, msg="提问成功，已生成工单")


@router.post("/tickets/{ticket_id}/handle-reply")
def submit_handle_reply(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    allowed_status = {"processing", "waiting_customer", "reopened"}
    if _flow_status(ticket) not in allowed_status:
        return fail_response(400, "当前状态不能继续处理")
    if not _can_change_status(user, ticket) and not _is_collaborator(user, ticket):
        return fail_response(403, "仅处理人或协作者可以提交处理结果")
    reply = str(body.get("reply") or "").strip()
    solution = str(body.get("solution") or "").strip()
    if not reply:
        return fail_response(400, "请填写处理记录")
    if not solution:
        return fail_response(400, "请填写解决方案")
    ticket.handler_reply = reply
    ticket.handler_solution = solution
    if body.get("estimatedResolveAt"):
        ticket.estimated_resolve_at = parse_dt(body.get("estimatedResolveAt"))
    if body.get("actualResolveAt"):
        ticket.actual_resolve_at = parse_dt(body.get("actualResolveAt"))
    resolution = str(body.get("resolution") or "").strip()
    if resolution:
        ticket.resolution = resolution
    internal = str(body.get("internalNote") or "").strip()
    attach_err = _save_ask_attachments(db, ticket, user, body.get("attachments"))
    if attach_err:
        db.rollback()
        return attach_err
    _add_log(db, ticket, user, "record", f"处理回答：{reply}\n解决方案：{solution}")
    if internal:
        _add_log(db, ticket, user, "internal", internal)
    db.commit()
    return ok(None, msg="已记录处理内容")


@router.post("/tickets/{ticket_id}/customer-feedback")
def customer_feedback(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    result = str(body.get("result") or "").strip()
    remark = str(body.get("remark") or "").strip()
    if result in {"confirmed", "rejected", "rate"}:
        if not _is_ticket_customer(user, ticket):
            return fail_response(403, "确认结案、评价和不认可只能由客户账号操作")
    elif not _is_admin(user) and not _is_ticket_customer(user, ticket):
        return fail_response(403, "仅工单所属客户可以反馈")
    if result == "confirmed":
        if ticket.status != "resolved":
            return fail_response(400, "仅已解决工单可以确认结案")
        rating_err = _apply_rating(ticket, body)
        if rating_err:
            return fail_response(400, rating_err)
        evaluation = remark or str(body.get("evaluation") or "").strip()
        if evaluation:
            ticket.evaluation = evaluation
        elif not ticket.evaluation:
            ticket.evaluation = "客户确认结案"
        if not ticket.actual_resolve_at:
            ticket.actual_resolve_at = ticket.status_changed_at or datetime.utcnow()
        ticket.pending_confirm = False
        _set_status(ticket, "closed")
        content = "客户确认结案"
        if ticket.rating:
            content = f"{content}，评价{ticket.rating}星"
        if evaluation:
            content = f"{content}：{evaluation}"
        _add_log(db, ticket, user, "confirm", content)
        db.commit()
        return ok(None, msg="已确认结案，工单已关闭")
    if result == "rate":
        if ticket.status != "closed":
            return fail_response(400, "仅已关闭工单可以补充评价")
        if ticket.rating:
            return fail_response(400, "该工单已评价")
        rating_err = _apply_rating(ticket, body)
        if rating_err:
            return fail_response(400, rating_err)
        if not ticket.rating:
            return fail_response(400, "请选择服务星级")
        evaluation = remark or str(body.get("evaluation") or "").strip()
        if evaluation:
            ticket.evaluation = evaluation
        content = f"客户评价{ticket.rating}星"
        if evaluation:
            content = f"{content}：{evaluation}"
        _add_log(db, ticket, user, "confirm", content)
        db.commit()
        return ok(None, msg="评价已提交")
    if result == "rejected":
        if ticket.status != "resolved":
            return fail_response(400, "仅已解决工单可以重新打开")
        if not remark:
            return fail_response(400, "请填写重新打开原因")
        ticket.evaluation = remark
        ticket.pending_confirm = False
        _restart_staff_sla(ticket)
        _set_status(ticket, "reopened")
        _add_log(db, ticket, user, "reopen", remark)
        db.commit()
        return ok(None, msg="已重新打开")
    if result == "solved":
        return fail_response(400, "请等待处理人标记已解决")
    if result == "supplement":
        if not remark:
            return fail_response(400, "请填写补充信息")
        if ticket.status in {"closed", "ended"}:
            return fail_response(400, "当前问题已结束，不能补充")
        open_for_supplement = {
            "unassigned",
            "pending",
            "processing",
            "waiting_customer",
            "resolved",
            "reopened",
            "overdue",
        }
        if ticket.status not in open_for_supplement:
            return fail_response(400, "当前状态不能补充信息")
        attach_err = _save_ask_attachments(db, ticket, user, body.get("attachments"))
        if attach_err:
            db.rollback()
            return attach_err
        if ticket.status in {"waiting_customer", "overdue"}:
            _restart_staff_sla(ticket)
            _set_status(ticket, "processing")
            _add_log(db, ticket, user, "record", remark)
            db.commit()
            return ok(None, msg="已补充，工单已回到处理中")
        _add_log(db, ticket, user, "record", remark)
        db.commit()
        return ok(None, msg="已补充")
    return fail_response(400, "请选择确认、评价、不认可、已解决或补充信息")


@router.post("/tickets/{ticket_id}/close")
def close_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if not _is_ticket_customer(user, ticket):
        return fail_response(403, "已解决工单请客户确认结案")
    if ticket.status != "resolved":
        return fail_response(400, "仅已解决工单可以关闭")
    resolution = str(body.get("resolution") or "").strip() or (ticket.resolution or "").strip()
    if resolution:
        ticket.resolution = resolution
    if body.get("actualResolveAt"):
        ticket.actual_resolve_at = parse_dt(body.get("actualResolveAt"))
    elif not ticket.actual_resolve_at:
        ticket.actual_resolve_at = datetime.utcnow()
    remark = str(body.get("remark") or "").strip() or "客户确认结案"
    ticket.pending_confirm = False
    _set_status(ticket, "closed")
    _add_log(db, ticket, user, "close", remark)
    db.commit()
    return ok(None, msg="工单已关闭")


@router.put("/tickets/{ticket_id}")
def update_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if not _can_edit_base(user, ticket):
        return fail_response(400, "仅待分派工单可以由管理员或客户编辑")
    title = str(body.get("title") or ticket.title or "").strip()
    description = str(body.get("description") or ticket.description or "").strip()
    if not title or not description:
        return fail_response(400, "标题和描述不能为空")
    changes = []
    if title != ticket.title:
        changes.append(f"标题：{ticket.title} → {title}")
    if description != (ticket.description or ""):
        changes.append("更新了问题描述")
    ticket.title = title[:200]
    ticket.description = description
    customer_editor = not _is_admin(user)
    if not customer_editor:
        if body.get("categoryId") and int(body["categoryId"]) != ticket.category_id:
            changes.append("更新了分类")
            ticket.category_id = int(body["categoryId"])
        if body.get("priorityId") and int(body["priorityId"]) != ticket.priority_id:
            changes.append("更新了优先级")
            ticket.priority_id = int(body["priorityId"])
        if body.get("customerId") and int(body["customerId"]) != ticket.customer_id:
            next_customer = db.get(Customer, int(body["customerId"]))
            if not next_customer:
                return fail_response(400, "客户不存在")
            if not next_customer.user_id:
                return fail_response(400, "请选择已绑定登录账号的客户")
            changes.append("更新了客户")
            ticket.customer_id = next_customer.id
        product = str(body.get("product") or ticket.product or "").strip()[:128]
        service_name = str(body.get("serviceName") or ticket.service_name or "").strip()[:128]
        order_no = str(body.get("orderNo") or ticket.order_no or "").strip()[:64]
        if product != (ticket.product or ""):
            changes.append(f"产品：{ticket.product or '-'} → {product}")
        if service_name and service_name != (ticket.service_name or ""):
            changes.append("更新了具体服务")
        if order_no and order_no != (ticket.order_no or ""):
            changes.append("更新了订单号")
        if product:
            product_err = _check_dict_value(db, "product", product, ticket.product)
            if product_err:
                return fail_response(400, product_err)
            ticket.product = product
        if service_name:
            service_err = _check_dict_value(db, "service", service_name, ticket.service_name)
            if service_err:
                return fail_response(400, service_err)
            ticket.service_name = service_name
        if order_no:
            ticket.order_no = order_no
        if "expectedFinishAt" in body:
            ticket.expected_finish_at = parse_dt(body.get("expectedFinishAt"))
            changes.append("更新了期望完成时间")
    if body.get("attachments"):
        attach_err = _save_ask_attachments(db, ticket, user, body.get("attachments"))
        if attach_err:
            db.rollback()
            return attach_err
        changes.append("更新了附件")
    ticket.updated_at = datetime.utcnow()
    _add_log(db, ticket, user, "edit", "；".join(changes) or "编辑工单基础信息")
    db.commit()
    return ok(None, msg="更新成功")


def _group_members(db: Session, group: HandlerGroup) -> list[User]:
    role_ids = [role.id for role in group.roles]
    if not role_ids:
        return []
    return (
        db.query(User)
        .join(User.roles)
        .filter(User.status == 1, Role.id.in_(role_ids))
        .distinct()
        .all()
    )


def _escalation_targets(db: Session) -> list[dict]:
    rows: list[dict] = []
    seen: set[int] = set()
    for group in db.query(HandlerGroup).order_by(HandlerGroup.id.asc()).all():
        if not group.leader_id or group.leader_id in seen:
            continue
        leader = group.leader
        if not leader or leader.status != 1:
            continue
        seen.add(leader.id)
        label = "管理员" if any(role.code == "admin" for role in leader.roles) else "负责人"
        rows.append(
            {
                "id": leader.id,
                "name": f"{_name(leader)}（{group.name}{label}）",
                "groupId": group.id,
            }
        )
    admin = (
        db.query(User)
        .join(User.roles)
        .filter(User.status == 1, Role.code == "admin")
        .order_by(User.id.asc())
        .first()
    )
    if admin and admin.id not in seen:
        admin_group = db.query(HandlerGroup).filter(HandlerGroup.name == "管理组").first()
        rows.append(
            {
                "id": admin.id,
                "name": f"{_name(admin)}（管理员）",
                "groupId": admin_group.id if admin_group else None,
            }
        )
    return rows


def _pick_assignee(db: Session, members: list[User]) -> User | None:
    if not members:
        return None
    member_ids = [user.id for user in members]
    rows = (
        db.query(Ticket.assignee_id, func.count(Ticket.id))
        .filter(Ticket.assignee_id.in_(member_ids), Ticket.status.in_(HANDLER_PENDING))
        .group_by(Ticket.assignee_id)
        .all()
    )
    counts = {user_id: count for user_id, count in rows}
    ordered = sorted(members, key=lambda user: (counts.get(user.id, 0), user.id))
    return ordered[0]


def _apply_owner(
    ticket: Ticket,
    body: dict,
    db: Session,
    exclude_assignee_id: int | None = None,
    cross_group: bool = False,
):
    group_id = body.get("groupId")
    if not group_id:
        return "请选择处理组"
    group = db.get(HandlerGroup, int(group_id))
    if not group:
        return "处理组不存在"
    if not group.roles:
        return "该组还没有分配角色"
    members = _group_members(db, group)
    if exclude_assignee_id:
        members = [user for user in members if user.id != exclude_assignee_id]
    assignee_id = body.get("assigneeId")
    if assignee_id and exclude_assignee_id and int(assignee_id) == exclude_assignee_id:
        return "不能转派给当前处理人"
    if assignee_id:
        assignee = db.get(User, int(assignee_id))
        if not assignee or assignee.status != 1 or not _is_staff(assignee):
            return "请选择后台工作人员"
        if any(role.code == "admin" for role in assignee.roles):
            return "转派不能分配给管理员，请使用升级"
        if cross_group and assignee not in members:
            own_group = _user_handler_group(assignee)
            if not own_group or own_group.name == "管理组":
                return "转派不能分配给管理员，请使用升级"
            group = own_group
        elif assignee not in members:
            return "处理人不属于该组"
    else:
        assignee = _pick_assignee(db, members)
        if not assignee:
            return "该组暂无其他可转派成员" if exclude_assignee_id else "该组暂无成员"
    ticket.assignee_id = assignee.id
    ticket.handler_group_id = group.id
    ticket.group_name = group.name
    if ticket.status in {"unassigned"}:
        _set_status(ticket, "pending")
    return None


@router.post("/tickets/{ticket_id}/assign")
def assign_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("ticket:assign")),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if ticket.status != "unassigned":
        return fail_response(400, "仅待分派工单可以派发")
    if not _is_admin(user):
        return fail_response(403, "待分派工单仅管理员可以派发")
    message = _apply_owner(ticket, body, db)
    if message:
        return fail_response(400, message)
    owner = _name(ticket.assignee) or "未指定处理人"
    group = ticket.group_name or "未指定处理组"
    how = "自动分配" if not body.get("assigneeId") else "指定处理人"
    _add_log(db, ticket, user, "assign", f"派发给 {owner}（{how}），处理组：{group}")
    db.commit()
    return ok(None, msg="派发成功")


@router.post("/tickets/{ticket_id}/transfer")
def transfer_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if _flow_status(ticket) not in {"pending", "processing", "reopened"}:
        return fail_response(400, "当前状态不能转派")
    if not _is_admin(user) and ticket.assignee_id != user.id:
        return fail_response(403, "仅管理员或工单负责人可以转派")
    group_id = body.get("groupId")
    group = db.get(HandlerGroup, int(group_id)) if group_id else None
    if group and group.name == "管理组":
        return fail_response(400, "转派不能分配给管理员，请使用升级")
    assignee_id = body.get("assigneeId")
    if assignee_id:
        target = db.get(User, int(assignee_id))
        if target and any(role.code == "admin" for role in target.roles):
            return fail_response(400, "转派不能分配给管理员，请使用升级")
    previous_id = ticket.assignee_id
    message = _apply_owner(
        ticket, body, db, exclude_assignee_id=ticket.assignee_id, cross_group=True
    )
    if message:
        return fail_response(400, message)
    picked = db.get(User, ticket.assignee_id) if ticket.assignee_id else None
    if picked and any(role.code == "admin" for role in picked.roles):
        db.rollback()
        return fail_response(400, "转派不能分配给管理员，请使用升级")
    _remember_former_assignee(db, ticket, previous_id)
    owner = _name(ticket.assignee) or "未指定处理人"
    group = ticket.group_name or "未指定处理组"
    _add_log(db, ticket, user, "transfer", f"转派给 {owner}，处理组：{group}")
    db.commit()
    return ok(None, msg="转派成功")


@router.put("/tickets/{ticket_id}/collaborators")
def set_collaborators(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if _flow_status(ticket) not in {"pending", "processing", "reopened"}:
        return fail_response(400, "当前状态不能调整协作者")
    if not _is_admin(user) and ticket.assignee_id != user.id:
        return fail_response(403, "仅管理员或工单负责人可以调整协作者")
    try:
        ids = [int(x) for x in (body.get("userIds") or [])]
    except (TypeError, ValueError):
        return fail_response(400, "协作者格式不正确")
    if ticket.assignee_id and ticket.assignee_id in ids:
        return fail_response(400, "协作者不能是工单负责人，请使用转派")
    users = db.query(User).filter(User.id.in_(ids)).all() if ids else []
    if any(not _is_staff(item) for item in users):
        return fail_response(400, "协作者只能选择后台工作人员")
    before = {u.id: _name(u) for u in ticket.collaborators}
    after = {u.id: _name(u) for u in users}
    ticket.collaborators = users
    added = [after[key] for key in after if key not in before]
    removed = [before[key] for key in before if key not in after]
    if added:
        _add_log(db, ticket, user, "collaborator", f"添加协作者：{'、'.join(added)}")
    if removed:
        _add_log(db, ticket, user, "collaborator", f"移除协作者：{'、'.join(removed)}")
    if not added and not removed:
        _add_log(db, ticket, user, "collaborator", "协作者未变化")
    db.commit()
    return ok(None, msg="已更新协作者")


@router.post("/tickets/{ticket_id}/notes")
def add_note(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("ticket:handle")),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if not _can_record(user, ticket):
        return fail_response(403, "只有处理人可以填写记录")
    content = str(body.get("content") or "").strip()
    if not content:
        return fail_response(400, "请填写内容")
    internal = bool(body.get("internal"))
    if body.get("estimatedResolveAt"):
        ticket.estimated_resolve_at = parse_dt(body.get("estimatedResolveAt"))
    action = "internal" if internal else "record"
    _add_log(db, ticket, user, action, content)
    db.commit()
    return ok(None, msg="已记录")


@router.post("/tickets/{ticket_id}/status")
def change_status(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    status = str(body.get("status") or "")
    current = _flow_status(ticket)
    transitions = {
        ("pending", "processing"),
        ("processing", "waiting_customer"),
        ("processing", "resolved"),
        ("reopened", "waiting_customer"),
        ("reopened", "resolved"),
    }
    if (current, status) not in transitions:
        return fail_response(400, "不能直接变更为该状态")
    if ticket.status in {"closed", "ended"}:
        return fail_response(400, "已结束工单不能变更状态")
    if not _can_change_status(user, ticket):
        return fail_response(403, "仅管理员或工单负责人可以修改状态")
    if _is_collaborator(user, ticket) and ticket.assignee_id != user.id and not _is_admin(user):
        return fail_response(403, "协作者不能变更工单状态")
    if status == "processing" and not ticket.assignee_id:
        return fail_response(400, "请先派发处理人")
    _set_status(ticket, status)
    if status == "resolved" and not ticket.actual_resolve_at:
        ticket.actual_resolve_at = datetime.utcnow()
    _add_log(db, ticket, user, "status", f"状态变更为{STATUS_LABEL[status]}")
    db.commit()
    return ok(None, msg="状态已更新")


@router.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("ticket:handle")),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    resolution = str(body.get("resolution") or "").strip()
    if not resolution:
        return fail_response(400, "请填写解决结果")
    if not _can_change_status(user, ticket):
        return fail_response(403, "仅管理员或当前处理人可以修改状态")
    ticket.resolution = resolution
    ticket.actual_resolve_at = parse_dt(body.get("actualResolveAt")) or datetime.utcnow()
    ticket.pending_confirm = False
    _set_status(ticket, "resolved")
    _add_log(db, ticket, user, "resolve", resolution)
    db.commit()
    return ok(None, msg="已标记解决")


@router.post("/tickets/{ticket_id}/confirm-request")
def request_confirm(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("ticket:handle")),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if ticket.status != "resolved":
        return fail_response(400, "请先将工单标记为已解决")
    ticket.pending_confirm = True
    _add_log(db, ticket, user, "confirm_request", "已提交客户确认")
    db.commit()
    return ok(None, msg="已提交客户确认")


@router.post("/tickets/{ticket_id}/confirm")
def confirm_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if not _is_ticket_customer(user, ticket):
        return fail_response(403, "确认结案只能由客户账号操作")
    if ticket.status != "resolved":
        return fail_response(400, "只有已解决的工单可以确认关闭")
    rating_err = _apply_rating(ticket, body)
    if rating_err:
        return fail_response(400, rating_err)
    ticket.evaluation = str(body.get("evaluation") or "").strip() or ticket.evaluation or "客户确认解决结果"
    if not ticket.actual_resolve_at:
        ticket.actual_resolve_at = ticket.status_changed_at or datetime.utcnow()
    ticket.pending_confirm = False
    _set_status(ticket, "closed")
    content = ticket.evaluation or "客户确认解决结果"
    if ticket.rating:
        content = f"{ticket.rating}星；{content}"
    _add_log(db, ticket, user, "confirm", content)
    db.commit()
    return ok(None, msg="工单已关闭")


@router.post("/tickets/{ticket_id}/reopen")
def reopen_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if ticket.status != "resolved":
        return fail_response(400, "仅已解决工单可以重新打开")
    if not _is_ticket_customer(user, ticket):
        return fail_response(403, "仅客户可以重新打开")
    reason = str(body.get("reason") or "").strip() or "重新打开工单"
    ticket.pending_confirm = False
    _restart_staff_sla(ticket)
    _set_status(ticket, "reopened")
    _add_log(db, ticket, user, "reopen", reason)
    db.commit()
    return ok(None, msg="工单已重新打开")


@router.post("/tickets/{ticket_id}/escalate")
def escalate_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("ticket:escalate")),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    _sync_overdue(db, [ticket])
    if ticket.status != "overdue" and sla_info(ticket)["slaState"] != "overdue":
        return fail_response(400, "仅超时工单可以升级")
    target = None
    if body.get("assigneeId"):
        target = db.get(User, int(body["assigneeId"]))
        if not target or target.status != 1:
            return fail_response(400, "升级对象不存在")
    else:
        target = _resolve_escalate_target(db, ticket)
    if not target:
        return fail_response(400, "没有可升级的负责人")
    reason = str(body.get("reason") or "").strip() or "处理超时，升级给负责人"
    if not _apply_escalate(
        db,
        ticket,
        operator=user,
        reason=reason,
        target=target,
        require_new_assignee=False,
    ):
        return fail_response(400, "仅超时工单可以升级")
    db.commit()
    return ok(None, msg="已升级")


@router.post("/tickets/{ticket_id}/followup")
def followup_ticket(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("ticket:followup")),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    if ticket.status != "closed":
        return fail_response(400, "仅已关闭工单可以回访")
    if not _is_admin(user) and not any(role.code == "cs" for role in user.roles):
        return fail_response(403, "仅管理员或客服可以回访")
    method = str(body.get("method") or "").strip()
    result = str(body.get("result") or "").strip()
    remark = str(body.get("remark") or body.get("evaluation") or "").strip()
    if method not in FOLLOWUP_METHODS:
        return fail_response(400, "请选择回访方式：电话、微信或上门")
    if result not in FOLLOWUP_RESULTS:
        return fail_response(400, "请选择回访结果：满意、一般、不满意或问题复发")
    followup_at = parse_dt(body.get("followupAt")) or datetime.utcnow()
    followup_user_id = body.get("followupUserId") or user.id
    try:
        followup_user_id = int(followup_user_id)
    except (TypeError, ValueError):
        return fail_response(400, "回访人不正确")
    followup_user = db.get(User, followup_user_id)
    if not followup_user or followup_user.status != 1:
        return fail_response(400, "回访人不存在")
    if not _is_admin(followup_user) and not any(role.code == "cs" for role in followup_user.roles):
        return fail_response(400, "回访人必须是管理员或客服")
    ticket.followup_method = method
    ticket.followup_result = result
    ticket.followup_remark = remark
    ticket.followup_at = followup_at
    ticket.followup_user_id = followup_user.id
    content = (
        f"回访人：{_name(followup_user)}；方式：{method}；结果：{result}；"
        f"时间：{fmt_dt(followup_at)}"
    )
    if remark:
        content = f"{content}；备注：{remark}"
    _add_log(db, ticket, user, "followup", content)
    db.commit()
    return ok(None, msg="已记录回访")


@router.post("/uploads")
async def upload_local_media(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        kind = "image"
    elif content_type.startswith("video/"):
        kind = "video"
    else:
        return fail_response(400, "请上传图片或视频")
    content = await file.read()
    if not content:
        return fail_response(400, "文件为空")
    if len(content) > MAX_SIZE:
        return fail_response(400, "文件不能超过 50MB")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix[:10].lower()
    stored = f"{uuid.uuid4().hex}{suffix}"
    (UPLOAD_DIR / stored).write_bytes(content)
    return ok(
        {
            "url": f"/api/media/{stored}",
            "filename": (file.filename or stored)[:255],
            "kind": kind,
        }
    )


@router.post("/tickets/{ticket_id}/attachments")
def add_attachment(
    ticket_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket, err = _get_ticket(db, ticket_id, user)
    if err:
        return err
    codes = user_permission_codes(user)
    if not _can_edit_base(user, ticket) and not codes.intersection({"ticket:create", "ticket:handle"}):
        return fail_response(403, "当前没有权限执行此操作")
    kind = str(body.get("kind") or "")
    url = str(body.get("url") or "").strip()
    filename = str(body.get("filename") or "附件").strip()[:255]
    if kind not in {"image", "video"}:
        return fail_response(400, "请上传图片或视频")
    if not (url.startswith("http") or url.startswith("/api/media/")):
        return fail_response(400, "附件地址无效")
    row = TicketAttachment(
        ticket_id=ticket.id,
        kind=kind,
        filename=filename or "附件",
        url=url[:512],
        stored_name="",
        size=0,
        uploader_id=user.id,
    )
    db.add(row)
    kind_label = "图片" if kind == "image" else "视频"
    _add_log(db, ticket, user, "attachment", f"上传{kind_label}：{row.filename}")
    db.commit()
    db.refresh(row)
    return ok({"id": row.id, "url": row.url}, msg="上传成功")


@router.delete("/tickets/attachments/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.get(TicketAttachment, attachment_id)
    if not row:
        return fail_response(404, "附件不存在")
    ticket, err = _get_ticket(db, row.ticket_id, user)
    if err:
        return err
    codes = user_permission_codes(user)
    can_edit = _can_edit_base(user, ticket)
    if not can_edit and not codes.intersection({"ticket:create", "ticket:handle"}):
        return fail_response(403, "当前没有权限执行此操作")
    filename = row.filename
    db.delete(row)
    _add_log(db, ticket, user, "attachment", f"删除附件：{filename}")
    db.commit()
    return ok(None, msg="已删除")


@router.get("/ticket-files/{attachment_id}")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.get(TicketAttachment, attachment_id)
    if not row:
        return fail_response(404, "附件不存在")
    ticket, err = _get_ticket(db, row.ticket_id, user)
    if err:
        return err
    path = UPLOAD_DIR / row.stored_name
    if not path.exists():
        return fail_response(404, "文件不存在")
    return FileResponse(path, filename=row.filename)
