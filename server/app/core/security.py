from datetime import datetime, timedelta, timezone
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def md5_hex(text: str) -> str:
    """与前端 CryptoJS.MD5(...).toString() 一致（32 位小写 hex）。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def hash_password(password_cipher: str) -> str:
    """入库：对客户端传来的 MD5 密文再做 bcrypt。"""
    return pwd_context.hash(password_cipher)


def verify_password(password_cipher: str, hashed: str) -> bool:
    """校验：password_cipher 为前端 MD5 后的密文。"""
    return pwd_context.verify(password_cipher, hashed)


def hash_plain_password(plain: str) -> str:
    """种子/测试：明文 → MD5 → bcrypt。"""
    return hash_password(md5_hex(plain))


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (JWTError, ValueError, TypeError):
        return None


def extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return authorization.strip() or None
