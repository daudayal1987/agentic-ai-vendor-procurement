from app.common.config import get_settings


def get_database_url() -> str:
    settings = get_settings()

    return (
        f"postgresql+psycopg://"
        f"{settings.database_user}:"
        f"{settings.database_password}@"
        f"{settings.database_host}:"
        f"{settings.database_port}/"
        f"{settings.database_name}"
    )