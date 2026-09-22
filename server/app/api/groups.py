from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.response import fail_response, ok
from app.db.session import get_db
from app.models import HandlerGroup, Role, User, handler_group_roles

router = APIRouter(prefix="/api", tags=["groups"])


def _name(user: User | None) -> str:
    if not user:
        return ""
    return user.display_name or user.username


def _group_members(db: Session, group: HandlerGroup) -> list[User]:
    role_ids = [role.id for role in group.roles]
    if not role_ids:
        return []
    return (
        db.query(User)
        .join(User.roles)
        .filter(User.status == 1, Role.id.in_(role_ids))
        .distinct()
        .order_by(User.id.asc())
        .all()
    )


def _group_data(db: Session, group: HandlerGroup) -> dict:
    members = _group_members(db, group)
    return {
        "id": group.id,
        "name": group.name,
        "roles": [{"id": role.id, "code": role.code, "name": role.name} for role in group.roles],
        "roleIds": [role.id for role in group.roles],
        "leaderId": group.leader_id,
        "leaderName": _name(group.leader),
        "members": [{"id": user.id, "name": _name(user)} for user in members],
    }


def _bind_roles(db: Session, group: HandlerGroup, role_ids: list[int]) -> str | None:
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all() if role_ids else []
    if len(roles) != len(set(role_ids)):
        return "角色不存在"
    if any(role.code == "customer" for role in roles):
        return "客户角色不能加入处理组"
    if role_ids:
        db.execute(
            delete(handler_group_roles).where(
                handler_group_roles.c.role_id.in_(role_ids),
                handler_group_roles.c.group_id != group.id,
            )
        )
    group.roles = roles
    return None


def _apply_leader(db: Session, group: HandlerGroup, body: dict) -> str | None:
    if group.name == "管理组":
        group.leader_id = None
        return None
    try:
        leader_id = body.get("leaderId")
        leader_id = int(leader_id) if leader_id not in (None, "") else None
    except (TypeError, ValueError):
        return "负责人格式不正确"
    return _set_leader(db, group, leader_id)


def _set_leader(db: Session, group: HandlerGroup, leader_id) -> str | None:
    if not leader_id:
        group.leader_id = None
        return None
    leader = db.get(User, int(leader_id))
    if not leader or leader.status != 1:
        return "负责人不存在"
    members = _group_members(db, group)
    if leader.id not in {user.id for user in members}:
        return "负责人必须是该组成员"
    group.leader_id = leader.id
    return None


@router.get("/handler-groups")
def list_groups(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("group:manage")),
):
    rows = db.query(HandlerGroup).order_by(HandlerGroup.id.asc()).all()
    return ok([_group_data(db, row) for row in rows])


@router.post("/handler-groups")
def create_group(
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("group:manage")),
):
    name = str(body.get("name") or "").strip()
    if not name:
        return fail_response(400, "请输入分组名称")
    if db.query(HandlerGroup).filter(HandlerGroup.name == name).first():
        return fail_response(400, "分组名称已存在")
    try:
        role_ids = [int(item) for item in (body.get("roleIds") or [])]
    except (TypeError, ValueError):
        return fail_response(400, "角色格式不正确")
    group = HandlerGroup(name=name[:64])
    db.add(group)
    db.flush()
    message = _bind_roles(db, group, role_ids)
    if message:
        db.rollback()
        return fail_response(400, message)
    message = _apply_leader(db, group, body)
    if message:
        db.rollback()
        return fail_response(400, message)
    db.commit()
    return ok({"id": group.id}, msg="创建成功")


@router.put("/handler-groups/{group_id}")
def update_group(
    group_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("group:manage")),
):
    group = db.get(HandlerGroup, group_id)
    if not group:
        return fail_response(404, "分组不存在")
    name = str(body.get("name") or "").strip()
    if not name:
        return fail_response(400, "请输入分组名称")
    exists = (
        db.query(HandlerGroup)
        .filter(HandlerGroup.name == name, HandlerGroup.id != group.id)
        .first()
    )
    if exists:
        return fail_response(400, "分组名称已存在")
    try:
        role_ids = [int(item) for item in (body.get("roleIds") or [])]
    except (TypeError, ValueError):
        return fail_response(400, "角色格式不正确")
    group.name = name[:64]
    message = _bind_roles(db, group, role_ids)
    if message:
        db.rollback()
        return fail_response(400, message)
    message = _apply_leader(db, group, body)
    if message:
        db.rollback()
        return fail_response(400, message)
    db.commit()
    return ok(None, msg="保存成功")


@router.delete("/handler-groups/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("group:manage")),
):
    group = db.get(HandlerGroup, group_id)
    if not group:
        return fail_response(404, "分组不存在")
    if group.name == "管理组":
        return fail_response(400, "管理组不能删除")
    db.delete(group)
    db.commit()
    return ok(None, msg="删除成功")
