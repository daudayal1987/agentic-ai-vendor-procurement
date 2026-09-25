from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from app.auth.jwt import decode_access_token
from app.common.config import get_settings


def test_expired_token_is_rejected():
    settings = get_settings()

    expired_time = datetime.now(timezone.utc) - timedelta(
        minutes=1
    )

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "iat": expired_time - timedelta(minutes=5),
            "exp": expired_time,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)