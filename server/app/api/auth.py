from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import build_menus, get_current_user, resolve_home_path, user_permission_codes
from app.core.response import envelope, fail_response, ok
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RoleBrief
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ChangePasswordRequest(BaseModel):
    """oldPassword / newPassword 均为前端 CryptoJS.MD5 后的 32 位 hex。"""

    oldPassword: str = Field(min_length=32, max_length=32)
    newPassword: str = Field(min_length=32, max_length=32)


def _user_me(user: User) -> dict:
    codes = sorted(user_permission_codes(user))
    code_set = set(codes)
    menus = build_menus(code_set)
    return {
        "id": user.id,
        "username": user.username,
        "displayName": user.display_name,
        # 兼容前端 header 字段
        "name": user.display_name or user.username,
        "jobNumber": user.username,
        "roles": [
            {"id": r.id, "code": r.code, "name": r.name} for r in user.roles
        ],
        "permissions": codes,
        "menus": menus,
        "homePath": resolve_home_path(code_set),
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    # body.password 为前端 CryptoJS.MD5 密文
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        return fail_response(401, "用户名或密码错误")
    if user.status != 1:
        return fail_response(401, "用户已停用")
    token = create_access_token(user.id)
    return ok({"token": token, "user": _user_me(user)})


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(_user_me(user))


@router.put("/password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(body.oldPassword, user.password_hash):
        return fail_response(400, "旧密码不正确")
    user.password_hash = hash_password(body.newPassword)
    db.add(user)
    db.commit()
    return ok(None, msg="密码修改成功")
