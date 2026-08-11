from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from core.config import settings
from database import get_db
from models import TokenBlacklist, User

logger = logging.getLogger("cozy.auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "jti": uuid.uuid4().hex})
    secret = settings.resolved_jwt_secret()
    return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    secret = settings.resolved_jwt_secret()
    try:
        return jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except InvalidTokenError as exc:
        logger.debug("JWT decode failed: %s", exc)
        raise exc


def is_token_revoked(db: Session, jti: str) -> bool:
    """Return True if the given token id has been blacklisted."""
    return (
        db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first() is not None
    )


def revoke_token(db: Session, token: str, user_id: int) -> bool:
    """Blacklist a token by its jti so it can no longer authenticate.

    Returns True when the token was actually revoked, False when it was
    already invalid/expired (nothing to revoke).
    """
    try:
        payload = decode_token(token)
    except InvalidTokenError:
        return False
    jti = payload.get("jti")
    if not jti:
        return False

    exp = payload.get("exp")
    try:
        expires_at = datetime.fromtimestamp(exp, tz=UTC) if exp else datetime.now(UTC)
    except (TypeError, ValueError, OSError):
        expires_at = datetime.now(UTC)

    if is_token_revoked(db, jti):
        return True

    db.add(
        TokenBlacklist(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at,
        )
    )
    db.commit()
    return True


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        email: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        if email is None:
            raise credentials_exception
        if jti and is_token_revoked(db, jti):
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception from None

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
