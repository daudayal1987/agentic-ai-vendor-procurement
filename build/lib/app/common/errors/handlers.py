from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.errors.exceptions import ApplicationError


def application_error_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    status_code = 400

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            }
        },
    )