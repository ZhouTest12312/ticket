from collections import defaultdict

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import fail_response
from app.core.security import decode_access_token, extract_token
from app.db.session import get_db
from app.models import User

PERMISSION_MSG = "当前没有权限执行此操作"


def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    token = extract_token(authorization)
    if not token:
        # FastAPI dependency cannot return JSONResponse easily for all cases;
        # raise via a small pattern using HTTPException-like custom.
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="请先登录")
    user_id = decode_access_token(token)
    if user_id is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="请先登录")
    user = db.get(User, user_id)
    if not user or user.status != 1:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="请先登录")
    return user


def user_permission_codes(user: User) -> set[str]:
    codes: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            codes.add(perm.code)
    return codes


def require_permissions(*needed: str):
    def _dep(user: User = Depends(get_current_user)) -> User:
        have = user_permission_codes(user)
        if not set(needed).issubset(have):
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail=PERMISSION_MSG)
        return user

    return _dep


def build_menus(permission_codes: set[str]) -> list[dict]:
    """按权限拼菜单；任意已登录用户至少有首页，避免 menus=[] 无法进系统。"""
    menus: list[dict] = [
        {
            "path": "/welcome",
            "component": "/welcome",
            "meta": {"title": "首页", "icon": "HomeOutlined"},
        }
    ]

    system_children: list[dict] = []
    if "user:read" in permission_codes or "user:write" in permission_codes:
        system_children.append(
            {
                "path": "/system/user",
                "component": "/system/user",
                "meta": {"title": "用户管理"},
            }
        )
    if "role:read" in permission_codes or "role:write" in permission_codes:
        system_children.append(
            {
                "path": "/system/role",
                "component": "/system/role",
                "meta": {"title": "角色管理"},
            }
        )
    if "group:manage" in permission_codes:
        system_children.append(
            {
                "path": "/system/group",
                "component": "/system/group",
                "meta": {"title": "角色分组"},
            }
        )
    if "dict:manage" in permission_codes:
        system_children.append(
            {
                "path": "/system/dict",
                "component": "/system/dict",
                "meta": {"title": "字典管理"},
            }
        )
    if system_children:
        menus.append(
            {
                "path": "/system",
                "component": "/system",
                "meta": {"title": "系统管理", "icon": "SettingOutlined"},
                "children": system_children,
            }
        )

    ticket_children: list[dict] = []
    staff_ticket = permission_codes.intersection(
        {
            "ticket:create",
            "ticket:assign",
            "ticket:handle",
            "ticket:view_all",
        }
    )
    if staff_ticket:
        ticket_children.append(
            {
                "path": "/ticket/list",
                "component": "/ticket",
                "meta": {"title": "工单列表"},
            }
        )
    if "customer:manage" in permission_codes:
        ticket_children.append(
            {
                "path": "/ticket/customer",
                "component": "/customer",
                "meta": {"title": "客户管理"},
            }
        )
    if "ticket:ask" in permission_codes or (
        "ticket:view_own" in permission_codes and not staff_ticket
    ):
        ticket_children.append(
            {
                "path": "/ticket/questions",
                "component": "/ticket/questions",
                "meta": {"title": "我的提问"},
            }
        )
    if ticket_children:
        menus.append(
            {
                "path": "/ticket",
                "component": "/ticket/layout",
                "redirect": ticket_children[0]["path"],
                "meta": {"title": "工单管理", "icon": "FileOutlined"},
                "children": ticket_children,
            }
        )

    return menus


def resolve_home_path(permission_codes: set[str]) -> str:
    if (
        "role:read" in permission_codes
        or "user:read" in permission_codes
        or "user:assign_role" in permission_codes
    ):
        return "/system/role"
    staff_ticket = permission_codes.intersection(
        {"ticket:create", "ticket:handle", "ticket:view_all", "ticket:assign"}
    )
    if staff_ticket:
        return "/ticket/list"
    if "ticket:ask" in permission_codes or "ticket:view_own" in permission_codes:
        return "/ticket/questions"
    if "customer:manage" in permission_codes:
        return "/ticket/customer"
    if "dict:manage" in permission_codes:
        return "/system/dict"
    return "/welcome"


def group_permissions(perms) -> list[dict]:
    grouped: dict[str, list] = defaultdict(list)
    for p in perms:
        grouped[p.module].append({"id": p.id, "code": p.code, "name": p.name})
    return [{"module": m, "items": items} for m, items in grouped.items()]
