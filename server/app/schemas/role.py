from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    permissionIds: list[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    permissionIds: list[int] = Field(default_factory=list)


class RoleOut(BaseModel):
    id: int
    code: str
    name: str
    description: str
    isSystem: bool
    permissionIds: list[int] = Field(default_factory=list)
