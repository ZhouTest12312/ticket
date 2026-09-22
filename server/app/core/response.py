from typing import Any

from fastapi.responses import JSONResponse


def envelope(code: int, data: Any = None, msg: str = "ok") -> dict:
    return {"code": code, "data": data, "msg": msg}


def ok(data: Any = None, msg: str = "ok") -> dict:
    return envelope(200, data, msg)


def fail_response(code: int, msg: str) -> JSONResponse:
    # Keep HTTP 200 so existing frontend interceptors read business code.
    return JSONResponse(status_code=200, content=envelope(code, None, msg))
