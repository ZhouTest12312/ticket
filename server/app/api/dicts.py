import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.response import fail_response, ok
from app.db.session import get_db
from app.models import DictItem, DictType, User

router = APIRouter(prefix="/api", tags=["dicts"])


def _type_by_code(db: Session, code: str) -> DictType | None:
    return db.query(DictType).filter(DictType.code == code).first()


def _item_out(row: DictItem, type_code: str) -> dict:
    return {
        "id": row.id,
        "typeCode": type_code,
        "name": row.name,
        "sort": row.sort,
        "status": row.status,
    }


def _parse_item(body: dict, *, partial: bool = False):
    name = str(body.get("name") or "").strip()[:128]
    status = body.get("status", 1)
    sort = body.get("sort", 0)
    if not partial or "name" in body:
        if not name:
            return None, "请输入字典项名称"
    try:
        status = int(status)
        sort = int(sort)
    except (TypeError, ValueError):
        return None, "排序或状态不正确"
    if status not in (0, 1):
        return None, "状态不正确"
    if sort < 0 or sort > 9999:
        return None, "排序范围为 0 到 9999"
    return {"name": name, "status": status, "sort": sort}, None


@router.get("/dict-types")
def list_dict_types(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("dict:manage")),
):
    rows = db.query(DictType).order_by(DictType.sort.asc(), DictType.id.asc()).all()
    return ok(
        [
            {
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "itemCount": len(row.items),
            }
            for row in rows
        ]
    )


@router.post("/dict-types")
def create_dict_type(
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("dict:manage")),
):
    name = str(body.get("name") or "").strip()[:64]
    if not name:
        return fail_response(400, "请输入字典类型")
    exists = db.query(DictType).filter(DictType.name == name).first()
    if exists:
        return fail_response(400, "字典类型已存在")
    max_sort = db.query(func.max(DictType.sort)).scalar() or 0
    row = DictType(code=f"d{uuid.uuid4().hex[:12]}", name=name, sort=int(max_sort) + 1)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ok(
        {"id": row.id, "code": row.code, "name": row.name, "itemCount": 0},
        msg="创建成功",
    )


@router.put("/dict-types/{type_id}")
def update_dict_type(
    type_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("dict:manage")),
):
    row = db.get(DictType, type_id)
    if not row:
        return fail_response(404, "字典不存在")
    name = str(body.get("name") or "").strip()[:64]
    if not name:
        return fail_response(400, "请输入字典类型")
    exists = (
        db.query(DictType)
        .filter(DictType.name == name, DictType.id != row.id)
        .first()
    )
    if exists:
        return fail_response(400, "字典类型已存在")
    row.name = name
    db.commit()
    return ok(None, msg="更新成功")


@router.delete("/dict-types/{type_id}")
def delete_dict_type(
    type_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("dict:manage")),
):
    row = db.get(DictType, type_id)
    if not row:
        return fail_response(404, "字典不存在")
    db.query(DictItem).filter(DictItem.type_id == row.id).delete()
    db.delete(row)
    db.commit()
    return ok(None, msg="删除成功")


@router.get("/dict-items")
def list_dict_items(
    typeCode: str = "",
    page: int = 1,
    pageSize: int = 10,
    name: str = "",
    status: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("dict:manage")),
):
    dtype = _type_by_code(db, typeCode.strip())
    if not dtype:
        return fail_response(400, "字典类型不存在")
    query = db.query(DictItem).filter(DictItem.type_id == dtype.id)
    if name.strip():
        query = query.filter(DictItem.name.like(f"%{name.strip()}%"))
    if status is not None:
        query = query.filter(DictItem.status == status)
    total = query.count()
    rows = (
        query.order_by(DictItem.sort.asc(), DictItem.id.asc())
        .offset(max(page - 1, 0) * pageSize)
        .limit(pageSize)
        .all()
    )
    return ok({"records": [_item_out(row, dtype.code) for row in rows], "total": total})


@router.get("/dict-items/{item_id}")
def get_dict_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("dict:manage")),
):
    row = db.get(DictItem, item_id)
    if not row or not row.dict_type:
        return fail_response(404, "字典项不存在")
    return ok(_item_out(row, row.dict_type.code))


@router.post("/dict-items")
def create_dict_item(
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("dict:manage")),
):
    dtype = _type_by_code(db, str(body.get("typeCode") or "").strip())
    if not dtype:
        return fail_response(400, "字典类型不存在")
    parsed, err = _parse_item(body)
    if err:
        return fail_response(400, err)
    exists = (
        db.query(DictItem)
        .filter(DictItem.type_id == dtype.id, DictItem.name == parsed["name"])
        .first()
    )
    if exists:
        return fail_response(400, "字典项已存在")
    row = DictItem(type_id=dtype.id, **parsed)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ok(_item_out(row, dtype.code), msg="创建成功")


@router.put("/dict-items/{item_id}")
def update_dict_item(
    item_id: int,
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("dict:manage")),
):
    row = db.get(DictItem, item_id)
    if not row or not row.dict_type:
        return fail_response(404, "字典项不存在")
    parsed, err = _parse_item(body)
    if err:
        return fail_response(400, err)
    exists = (
        db.query(DictItem)
        .filter(
            DictItem.type_id == row.type_id,
            DictItem.name == parsed["name"],
            DictItem.id != row.id,
        )
        .first()
    )
    if exists:
        return fail_response(400, "字典项已存在")
    row.name = parsed["name"]
    row.sort = parsed["sort"]
    row.status = parsed["status"]
    db.commit()
    return ok(None, msg="更新成功")


@router.delete("/dict-items/{item_id}")
def delete_dict_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("dict:manage")),
):
    row = db.get(DictItem, item_id)
    if not row:
        return fail_response(404, "字典项不存在")
    db.delete(row)
    db.commit()
    return ok(None, msg="删除成功")
