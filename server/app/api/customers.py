import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.response import fail_response, ok
from app.db.session import get_db
from app.models import Customer, Ticket, User
from app.ticket_flow import STATUS_LABEL, fmt_dt

router = APIRouter(prefix="/api", tags=["customers"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[\d\-+() ]{6,20}$")


def _clean(value, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _parse_customer(body: dict, *, partial: bool = False):
    name = _clean(body.get("name"), 128)
    contact = _clean(body.get("contactName"), 64)
    phone = _clean(body.get("phone"), 32)
    email = _clean(body.get("email"), 128)
    industry = _clean(body.get("industry"), 64)
    status = body.get("status", 1)
    if not partial or "name" in body:
        if not name:
            return None, "请输入客户名称"
    if not partial or "contactName" in body:
        if not contact:
            return None, "请输入联系人"
    if not partial or "phone" in body:
        if not phone or not PHONE_RE.fullmatch(phone):
            return None, "请输入有效电话"
    if email and not EMAIL_RE.fullmatch(email):
        return None, "邮箱格式不正确"
    if not partial or "industry" in body:
        if not industry:
            return None, "请输入所属行业"
    try:
        status = int(status)
    except (TypeError, ValueError):
        return None, "状态不正确"
    if status not in (0, 1):
        return None, "状态不正确"
    return {
        "name": name,
        "contact_name": contact,
        "phone": phone,
        "email": email,
        "industry": industry,
        "status": status,
        "user_id": body.get("userId"),
    }, None


def _bind_user(db: Session, row: Customer, user_id) -> str | None:
    if user_id in (None, ""):
        row.user_id = None
        return None
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return "登录账号不正确"
    user = db.get(User, user_id)
    if not user or user.status != 1:
        return "登录账号不存在"
    if not any(role.code == "customer" for role in user.roles):
        return "只能绑定客户角色账号"
    taken = (
        db.query(Customer)
        .filter(Customer.user_id == user.id, Customer.id != row.id)
        .first()
    )
    if taken:
        return "该账号已绑定其他客户"
    row.user_id = user.id
    return None


def _customer_out(row: Customer) -> dict:
    user = row.user
    return {
        "id": row.id,
        "name": row.name,
        "contactName": row.contact_name,
        "phone": row.phone,
        "email": row.email,
        "industry": row.industry,
        "status": row.status,
        "userId": row.user_id,
        "userName": (user.display_name or user.username) if user else "",
        "createdAt": fmt_dt(row.created_at),
    }


@router.get("/customers")
def list_customers(
    page: int = 1,
    pageSize: int = 10,
    name: str = "",
    contact: str = "",
    status: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("customer:manage")),
):
    q = db.query(Customer)
    if name.strip():
        q = q.filter(Customer.name.like(f"%{name.strip()}%"))
    if contact.strip():
        q = q.filter(Customer.contact_name.like(f"%{contact.strip()}%"))
    if status is not None:
        q = q.filter(Customer.status == status)
    total = q.count()
    items = (
        q.order_by(Customer.id.desc())
        .offset(max(page - 1, 0) * pageSize)
        .limit(pageSize)
        .all()
    )
    return ok({"records": [_customer_out(r) for r in items], "total": total})


@router.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("customer:manage")),
):
    row = db.get(Customer, customer_id)
    if not row:
        return fail_response(404, "客户不存在")
    return ok(_customer_out(row))


@router.post("/customers")
def create_customer(
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("customer:manage")),
):
    data, err = _parse_customer(body)
    if err:
        return fail_response(400, err)
    user_id = data.pop("user_id", None)
    row = Customer(**data)
    db.add(row)
    db.flush()
    message = _bind_user(db, row, user_id)
    if message:
        db.rollback()
        return fail_response(400, message)
    db.commit()
    db.refresh(row)
    return ok({"id": row.id}, msg="创建成功")


@router.put("/customers/{customer_id}")
def update_customer(
    customer_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("customer:manage")),
):
    row = db.get(Customer, customer_id)
    if not row:
        return fail_response(404, "客户不存在")
    data, err = _parse_customer(body)
    if err:
        return fail_response(400, err)
    user_id = data.pop("user_id", None)
    for key, value in data.items():
        setattr(row, key, value)
    message = _bind_user(db, row, user_id)
    if message:
        db.rollback()
        return fail_response(400, message)
    db.commit()
    return ok(None, msg="更新成功")


@router.get("/customers/{customer_id}/tickets")
def list_customer_tickets(
    customer_id: int,
    page: int = 1,
    pageSize: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("customer:manage")),
):
    row = db.get(Customer, customer_id)
    if not row:
        return fail_response(404, "客户不存在")
    q = db.query(Ticket).filter(Ticket.customer_id == customer_id)
    total = q.count()
    items = (
        q.order_by(Ticket.id.desc())
        .offset(max(page - 1, 0) * pageSize)
        .limit(pageSize)
        .all()
    )
    records = [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "statusLabel": STATUS_LABEL.get(t.status, t.status),
            "createdAt": fmt_dt(t.created_at),
        }
        for t in items
    ]
    return ok({"records": records, "total": total})
