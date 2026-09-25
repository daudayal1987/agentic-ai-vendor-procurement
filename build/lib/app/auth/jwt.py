from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.common.config import get_settings


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> UUID:
    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    subject = payload.get("sub")

    if not subject:
        raise ValueError("Token subject is missing")

    return UUID(subject)