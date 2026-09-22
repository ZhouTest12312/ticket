from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.response import fail_response, ok
from app.core.security import hash_plain_password
from app.db.session import get_db
from app.models import Permission, Role, User

router = APIRouter(prefix="/api", tags=["rbac"])

DEFAULT_PASSWORD = "admin123"


def _user_groups(user: User) -> list[dict]:
    seen: dict[int, str] = {}
    for role in user.roles:
        for group in role.handler_groups:
            seen[group.id] = group.name
    return [{"id": group_id, "name": name} for group_id, name in seen.items()]


def _single_admin_message(db: Session, user_id: int | None, role_ids: list[int]) -> str | None:
    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if not admin_role:
        return None
    user = db.get(User, user_id) if user_id else None
    if user and user.username == "admin" and admin_role.id not in role_ids:
        return "不能取消管理员账号的「管理员」角色"
    if admin_role.id not in role_ids:
        return None
    others = (
        db.query(User)
        .join(User.roles)
        .filter(Role.id == admin_role.id, User.id != (user_id or 0))
        .count()
    )
    if others:
        return "管理员只能有一个"
    return None


@router.get("/permissions")
def list_permissions(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:read")),
):
    from app.api.deps import group_permissions

    perms = db.query(Permission).order_by(Permission.module, Permission.id).all()
    return ok(group_permissions(perms))


@router.get("/roles")
def list_roles(
    page: int = 1,
    pageSize: int = 10,
    keyword: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:read")),
):
    q = db.query(Role)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter((Role.name.like(like)) | (Role.code.like(like)))
    total = q.count()
    items = (
        q.order_by(Role.id.asc())
        .offset(max(page - 1, 0) * pageSize)
        .limit(pageSize)
        .all()
    )
    records = [
        {
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "isSystem": r.is_system,
        }
        for r in items
    ]
    return ok({"records": records, "total": total})


@router.get("/roles/{role_id}")
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:read")),
):
    role = db.get(Role, role_id)
    if not role:
        return fail_response(404, "角色不存在")
    return ok(
        {
            "id": role.id,
            "code": role.code,
            "name": role.name,
            "description": role.description,
            "isSystem": role.is_system,
            "permissionIds": [p.id for p in role.permissions],
        }
    )


@router.post("/roles")
def create_role(
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:write")),
):
    code = (body.get("code") or "").strip()
    name = (body.get("name") or "").strip()
    description = body.get("description") or ""
    permission_ids = body.get("permissionIds") or []
    if not code or not name:
        return fail_response(400, "角色编码和名称不能为空")
    exists = db.query(Role).filter(Role.code == code).first()
    if exists:
        return fail_response(400, "角色编码已存在")
    role = Role(code=code, name=name, description=description, is_system=False)
    if permission_ids:
        perms = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        role.permissions = perms
    db.add(role)
    db.commit()
    db.refresh(role)
    return ok({"id": role.id}, msg="创建成功")


@router.put("/roles/{role_id}")
def update_role(
    role_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:write")),
):
    role = db.get(Role, role_id)
    if not role:
        return fail_response(404, "角色不存在")
    name = (body.get("name") or "").strip()
    if not name:
        return fail_response(400, "角色名称不能为空")
    role.name = name
    role.description = body.get("description") or ""
    permission_ids = body.get("permissionIds") or []
    perms = (
        db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        if permission_ids
        else []
    )
    role.permissions = perms
    db.commit()
    return ok(None, msg="更新成功")


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("role:write")),
):
    from sqlalchemy import func, select

    from app.models import user_roles

    role = db.get(Role, role_id)
    if not role:
        return fail_response(404, "角色不存在")
    if role.is_system:
        return fail_response(400, "系统角色不可删除")
    # 直接查关联表，避免 relationship 未加载导致误删
    user_count = db.execute(
        select(func.count())
        .select_from(user_roles)
        .where(user_roles.c.role_id == role_id)
    ).scalar_one()
    if user_count > 0:
        return fail_response(
            400,
            f"角色「{role.name}」已分配给 {user_count} 个用户，请先在「用户管理」中取消后再删除",
        )
    db.delete(role)
    db.commit()
    return ok(None, msg="删除成功")


@router.get("/users")
def list_users(
    page: int = 1,
    pageSize: int = 10,
    keyword: str = "",
    roleId: int | None = None,
    excludeRoleId: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("user:read")),
):
    q = db.query(User)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter((User.username.like(like)) | (User.display_name.like(like)))
    if roleId is not None:
        q = q.filter(User.roles.any(Role.id == roleId))
    if excludeRoleId is not None:
        q = q.filter(~User.roles.any(Role.id == excludeRoleId))
    total = q.count()
    items = (
        q.order_by(User.id.asc())
        .offset(max(page - 1, 0) * pageSize)
        .limit(pageSize)
        .all()
    )
    records = [
        {
            "id": u.id,
            "username": u.username,
            "displayName": u.display_name,
            "status": u.status,
            "roles": [{"id": r.id, "code": r.code, "name": r.name} for r in u.roles],
            "groups": _user_groups(u),
        }
        for u in items
    ]
    return ok({"records": records, "total": total})


@router.post("/users")
def create_user(
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("user:write")),
):
    username = str(body.get("username") or "").strip()
    display_name = str(body.get("displayName") or "").strip()
    if not username:
        return fail_response(400, "请输入用户名")
    if len(username) > 64:
        return fail_response(400, "用户名过长")
    if not display_name:
        return fail_response(400, "请输入显示名")
    if db.query(User).filter(User.username == username).first():
        return fail_response(400, "用户名已存在")
    try:
        role_ids = [int(item) for item in (body.get("roleIds") or [])]
    except (TypeError, ValueError):
        return fail_response(400, "角色格式不正确")
    message = _single_admin_message(db, None, role_ids)
    if message:
        return fail_response(400, message)
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all() if role_ids else []
    password = str(body.get("password") or "").strip() or DEFAULT_PASSWORD
    user = User(
        username=username,
        display_name=display_name[:128],
        password_hash=hash_plain_password(password),
        status=1,
        roles=roles,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok({"id": user.id}, msg="创建成功，默认密码为 admin123")


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("user:write")),
):
    user = db.get(User, user_id)
    if not user:
        return fail_response(404, "用户不存在")
    display_name = str(body.get("displayName") or "").strip()
    if not display_name:
        return fail_response(400, "请输入显示名")
    try:
        role_ids = [int(item) for item in (body.get("roleIds") or [])]
    except (TypeError, ValueError):
        return fail_response(400, "角色格式不正确")
    message = _single_admin_message(db, user.id, role_ids)
    if message:
        return fail_response(400, message)
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all() if role_ids else []
    user.display_name = display_name[:128]
    if "status" in body:
        user.status = 1 if int(body.get("status") or 0) == 1 else 0
        if user.username == "admin":
            user.status = 1
    user.roles = roles
    password = str(body.get("password") or "").strip()
    if password:
        user.password_hash = hash_plain_password(password)
    db.commit()
    return ok(None, msg="保存成功")


@router.put("/users/{user_id}/roles")
def assign_roles(
    user_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("user:assign_role")),
):
    user = db.get(User, user_id)
    if not user:
        return fail_response(404, "用户不存在")
    role_ids = body.get("roleIds") or []
    # 统一 int，避免前端 number/string 混用
    try:
        role_ids = [int(x) for x in role_ids]
    except (TypeError, ValueError):
        return fail_response(400, "roleIds 格式不正确")
    # 保护内置 admin，防止误操作后失去管理入口
    if user.username == "admin":
        admin_role = db.query(Role).filter(Role.code == "admin").first()
        if admin_role and admin_role.id not in role_ids:
            return fail_response(400, "不能取消管理员账号的「管理员」角色")
    message = _single_admin_message(db, user.id, role_ids)
    if message:
        return fail_response(400, message)
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all() if role_ids else []
    user.roles = roles
    db.commit()
    return ok(None, msg="分配成功")
