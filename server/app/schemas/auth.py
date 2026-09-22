from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    # 前端 CryptoJS.MD5 后的 32 位 hex 密文
    password: str = Field(min_length=1)


class RoleBrief(BaseModel):
    id: int
    code: str
    name: str


class UserMe(BaseModel):
    id: int
    username: str
    displayName: str
    roles: list[RoleBrief]
    permissions: list[str]
    menus: list[dict]


class LoginData(BaseModel):
    token: str
    user: UserMe
