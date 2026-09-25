from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    environment: str


class ReadinessResponse(BaseModel):
    status: Literal["ready"]
    environment: str