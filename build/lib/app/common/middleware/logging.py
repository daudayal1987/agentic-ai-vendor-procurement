import time

from fastapi import Request

from app.common.logging import get_logger


logger = get_logger("http")


async def logging_middleware(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    request_id = getattr(
        request.state,
        "request_id",
        "unknown",
    )

    logger.info(
        "request_completed "
        "request_id=%s "
        "method=%s "
        "path=%s "
        "status_code=%s "
        "duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response