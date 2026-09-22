"""Seed permissions, system roles, and demo users. Idempotent."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import hash_plain_password
from app.models import (
    Customer,
    DictItem,
    DictType,
    HandlerGroup,
    Permission,
    Role,
    Ticket,
    TicketCategory,
    TicketLog,
    TicketPriority,
    User,
)

PERMISSIONS = [
    ("system", "role:read", "查看角色"),
    ("system", "role:write", "管理角色"),
    ("system", "user:read", "查看用户"),
    ("system", "user:write", "管理用户"),
    ("system", "user:assign_role", "分配角色"),
    ("system", "group:manage", "管理分组"),
    ("system", "dict:manage", "管理字典"),
    ("ticket", "ticket:create", "创建工单"),
    ("ticket", "ticket:assign", "分派工单"),
    ("ticket", "ticket:handle", "处理工单"),
    ("ticket", "ticket:escalate", "升级工单"),
    ("ticket", "ticket:followup", "回访工单"),
    ("ticket", "ticket:close", "关闭工单"),
    ("ticket", "ticket:view_own", "查看自己的工单"),
    ("ticket", "ticket:view_all", "查看全部工单"),
    ("ticket", "ticket:ask", "客户提问"),
    ("meta", "customer:manage", "管理客户"),
    ("meta", "category:manage", "管理分类"),
    ("meta", "priority:manage", "管理优先级"),
    ("meta", "rule:manage", "管理工单规则"),
]

ROLE_PERMS = {
    "admin": None,  # all
    "cs": [
        "role:read",
        "user:read",
        "ticket:create",
        "ticket:assign",
        "ticket:followup",
        "ticket:close",
        "ticket:escalate",
        "ticket:view_own",
        "customer:manage",
    ],
    "tech": ["ticket:handle", "ticket:escalate", "ticket:view_own"],
    "customer": ["ticket:view_own", "ticket:ask"],
}

ROLE_META = {
    "admin": ("管理员", "系统管理员，拥有全部权限"),
    "cs": ("客服人员", "创建工单、补充信息、跟进客户"),
    "tech": ("技术人员", "处理技术问题并更新方案"),
    "customer": ("客户", "查看问题进度并补充信息"),
}

USERS = [
    ("admin", "管理员", "admin"),
    ("cs01", "客服01", "cs"),
    ("tech01", "技术01", "tech"),
    ("customer01", "客户01", "customer"),
]

SEED_PASSWORD = "Admin@123"


def seed_all(db: Session) -> None:
    perm_by_code: dict[str, Permission] = {}
    for module, code, name in PERMISSIONS:
        existing = db.query(Permission).filter(Permission.code == code).first()
        if existing:
            perm_by_code[code] = existing
            continue
        p = Permission(code=code, name=name, module=module, description=name)
        db.add(p)
        db.flush()
        perm_by_code[code] = p

    role_by_code: dict[str, Role] = {}
    for code, (name, desc) in ROLE_META.items():
        role = db.query(Role).filter(Role.code == code).first()
        if not role:
            role = Role(code=code, name=name, description=desc, is_system=True)
            db.add(role)
            db.flush()
        codes = ROLE_PERMS[code]
        if codes is None:
            role.permissions = list(perm_by_code.values())
        else:
            role.permissions = [perm_by_code[c] for c in codes if c in perm_by_code]
        role_by_code[code] = role

    for username, display, role_code in USERS:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(
                username=username,
                password_hash=hash_plain_password(SEED_PASSWORD),
                display_name=display,
                status=1,
            )
            db.add(user)
            db.flush()
        else:
            # 已存在用户：只同步展示名/状态/角色，不覆盖 password_hash
            # （避免 init_db/seed 把改密结果刷回 SEED_PASSWORD）
            user.display_name = display
            user.status = 1
        user.roles = [role_by_code[role_code]]

    seed_ticket_meta(db)
    seed_handler_groups(db)
    seed_dictionaries(db)
    seed_demo_tickets(db)
    db.commit()


CATEGORIES = ["功能问题", "系统故障", "使用咨询", "其他"]
PRIORITIES = [
    ("低", 1, 72, 8),
    ("中", 2, 24, 4),
    ("高", 3, 4, 1),
    ("紧急", 4, 1, 0),
]


def seed_ticket_meta(db: Session) -> None:
    for index, name in enumerate(CATEGORIES):
        row = db.query(TicketCategory).filter(TicketCategory.name == name).first()
        if not row:
            db.add(TicketCategory(name=name, sort=index))
    for name, level, sla_hours, warn_hours in PRIORITIES:
        row = db.query(TicketPriority).filter(TicketPriority.name == name).first()
        if not row:
            db.add(
                TicketPriority(
                    name=name, level=level, sla_hours=sla_hours, warn_hours=warn_hours
                )
            )
        else:
            row.level = level
            row.sla_hours = sla_hours
            row.warn_hours = warn_hours


DEFAULT_HANDLER_GROUPS = (
    ("管理组", "admin"),
    ("客服组", "cs"),
    ("技术组", "tech"),
)


def _ensure_permission(db: Session, module: str, code: str, name: str) -> Permission:
    row = db.query(Permission).filter(Permission.code == code).first()
    if row:
        return row
    row = Permission(code=code, name=name, module=module, description=name)
    db.add(row)
    db.flush()
    return row


def seed_handler_groups(db: Session) -> None:
    extra = [
        ("system", "user:write", "管理用户"),
        ("system", "group:manage", "管理分组"),
    ]
    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if admin_role:
        have = {perm.code for perm in admin_role.permissions}
        for module, code, name in extra:
            perm = _ensure_permission(db, module, code, name)
            if code not in have:
                admin_role.permissions.append(perm)
    for code in ("cs", "tech", "customer"):
        role = db.query(Role).filter(Role.code == code).first()
        if not role:
            continue
        wanted = set(ROLE_PERMS[code])
        if {perm.code for perm in role.permissions} == wanted:
            continue
        role.permissions = [
            _ensure_permission(db, module, perm_code, name)
            for module, perm_code, name in PERMISSIONS
            if perm_code in wanted
        ]
    default_leaders = {
        "管理组": "admin",
        "客服组": "cs01",
        "技术组": "tech01",
    }
    for name, role_code in DEFAULT_HANDLER_GROUPS:
        group = db.query(HandlerGroup).filter(HandlerGroup.name == name).first()
        if not group:
            group = HandlerGroup(name=name)
            db.add(group)
            db.flush()
        role = db.query(Role).filter(Role.code == role_code).first()
        if role and not role.handler_groups:
            group.roles.append(role)
        if name == "管理组":
            group.leader_id = None
        elif not group.leader_id:
            leader = db.query(User).filter(User.username == default_leaders.get(name)).first()
            if leader:
                group.leader_id = leader.id


DICT_TYPES = [
    ("product", "产品", 1),
    ("service", "具体服务", 2),
]
DICT_ITEMS = {
    "product": ["校园管理平台", "在线课堂", "教务系统", "家校沟通"],
    "service": ["账号开通", "功能咨询", "故障排查", "数据导入", "培训支持"],
}


def seed_dictionaries(db: Session) -> None:
    perm = db.query(Permission).filter(Permission.code == "dict:manage").first()
    if not perm:
        perm = Permission(
            code="dict:manage", name="管理字典", module="system", description="管理字典"
        )
        db.add(perm)
        db.flush()
    admin = db.query(Role).filter(Role.code == "admin").first()
    if admin is not None and all(item.code != "dict:manage" for item in admin.permissions):
        admin.permissions.append(perm)
    for code, name, sort in DICT_TYPES:
        row = db.query(DictType).filter(DictType.code == code).first()
        if not row:
            row = DictType(code=code, name=name, sort=sort)
            db.add(row)
            db.flush()
        for index, item_name in enumerate(DICT_ITEMS.get(code, []), start=1):
            exists = (
                db.query(DictItem)
                .filter(DictItem.type_id == row.id, DictItem.name == item_name)
                .first()
            )
            if not exists:
                db.add(DictItem(type_id=row.id, name=item_name, sort=index, status=1))


DEMO_TICKETS = [
    {
        "title": "校园管理平台无法登录",
        "description": "老师反馈输入账号密码后页面没有反应，无法进入首页。",
        "category": "系统故障",
        "priority": "高",
        "product": "校园管理平台",
        "service": "账号开通",
        "order_no": "SO-202609-001",
        "status": "unassigned",
        "assignee": "",
    },
    {
        "title": "在线课堂视频无法播放",
        "description": "学生进入直播后黑屏，刷新多次仍然没有声音和画面。",
        "category": "功能问题",
        "priority": "紧急",
        "product": "在线课堂",
        "service": "故障排查",
        "order_no": "SO-202609-014",
        "status": "processing",
        "assignee": "tech01",
    },
    {
        "title": "教务系统成绩导出失败",
        "description": "导出本学期成绩时提示文件生成失败，已重试两次。",
        "category": "功能问题",
        "priority": "中",
        "product": "教务系统",
        "service": "数据导入",
        "order_no": "SO-202609-028",
        "status": "pending",
        "assignee": "cs01",
    },
]


def seed_demo_tickets(db: Session) -> None:
    customer = db.query(Customer).filter(Customer.name == "星河教育").first()
    if not customer:
        customer = Customer(
            name="星河教育",
            contact_name="王小敏",
            phone="13800001111",
            email="wang@example.com",
            industry="教育培训",
            status=1,
        )
        db.add(customer)
        db.flush()
    portal_user = db.query(User).filter(User.username == "customer01").first()
    if portal_user and not customer.user_id:
        customer.user_id = portal_user.id
    if not portal_user or customer.user_id != portal_user.id:
        return
    now = datetime.utcnow()
    for index, item in enumerate(DEMO_TICKETS):
        if db.query(Ticket).filter(Ticket.title == item["title"]).first():
            continue
        category = db.query(TicketCategory).filter(TicketCategory.name == item["category"]).first()
        priority = db.query(TicketPriority).filter(TicketPriority.name == item["priority"]).first()
        if not category or not priority:
            continue
        created = now + timedelta(seconds=index)
        ticket = Ticket(
            title=item["title"],
            description=item["description"],
            category_id=category.id,
            priority_id=priority.id,
            customer_id=customer.id,
            product=item["product"],
            order_no=f"ASK-{created.strftime('%Y%m%d%H%M%S')}{portal_user.id:04d}",
            service_name=item["service"],
            status="unassigned",
            source="ask",
            status_changed_at=created,
            creator_id=portal_user.id,
            created_at=created,
            updated_at=created,
        )
        db.add(ticket)
        db.flush()
        ticket.ticket_no = f"GD{now.strftime('%Y%m%d')}{ticket.id:04d}"
        db.add(
            TicketLog(
                ticket_id=ticket.id,
                action="ask",
                content=f"客户提问「{ticket.title}」",
                operator_id=portal_user.id,
            )
        )
