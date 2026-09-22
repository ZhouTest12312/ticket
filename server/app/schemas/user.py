from pydantic import BaseModel, Field

from app.schemas.auth import RoleBrief


class UserOut(BaseModel):
    id: int
    username: str
    displayName: str
    status: int
    roles: list[RoleBrief]


class AssignRolesRequest(BaseModel):
    roleIds: list[int] = Field(default_factory=list)
