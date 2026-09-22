from fastapi import FastAPI

from app.common.errors.exceptions import ApplicationError
from app.common.errors.handlers import application_error_handler
from app.common.middleware.request_id import request_id_middleware
from app.common.middleware.logging import logging_middleware

from app.common.config import get_settings
from app.common.logging import configure_logging

from app.api.router import api_router


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Enterprise Document Intelligence & Decision Assistant",
    version="0.1.0",
)

app.add_exception_handler(
    ApplicationError,
    application_error_handler,
)

app.middleware("http")(request_id_middleware)
app.middleware("http")(logging_middleware)

app.include_router(api_router)