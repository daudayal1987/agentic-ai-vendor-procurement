from uuid import UUID

from fastapi import Header

from app.auth.principal import AuthenticatedPrincipal


def get_current_principal(
    x_user_id: UUID = Header(...),
) -> AuthenticatedPrincipal:
    """
    Development-only identity source.

    Production:
    JWT -> authenticated principal -> user_id
    """
    return AuthenticatedPrincipal(
        user_id=x_user_id,
    )