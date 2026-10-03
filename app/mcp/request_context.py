from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from uuid import UUID

from mcp import MCPError
from mcp.server import ServerRequestContext

from app.tenants.context import TenantContext

REQUEST_CONTEXT_META_KEY = "enterprise/request-context"
DEFAULT_AUDIENCE = "enterprise-document-intelligence"

_request_context_var: ContextVar[MCPRequestContext | None] = ContextVar(
    "mcp_request_context",
    default=None,
)


@dataclass(frozen=True)
class MCPRequestContext:
    """Authenticated application identity for exactly one MCP request."""

    tenant_id: UUID
    user_id: UUID
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    enabled_services: tuple[str, ...]

    def to_tenant_context(self) -> TenantContext:
        return TenantContext(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            roles=self.roles,
            permissions=self.permissions,
            enabled_services=self.enabled_services,
        )


class RequestContextSigner:
    """Learning-only HMAC bearer token issuer/verifier.

    Production should replace this boundary with validation of a short-lived,
    audience-bound access token issued by the platform authentication system.
    The MCP client must not own the signing secret in production.
    """

    def __init__(
        self,
        secret: bytes,
        *,
        audience: str = DEFAULT_AUDIENCE,
        ttl_seconds: int = 300,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not secret:
            raise ValueError("secret must not be empty")
        if not audience:
            raise ValueError("audience must not be empty")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        self._secret = secret
        self._audience = audience
        self._ttl_seconds = ttl_seconds
        self._clock = clock

    def issue(self, context: MCPRequestContext) -> str:
        now = int(self._clock())
        payload = {
            "aud": self._audience,
            "exp": now + self._ttl_seconds,
            "iat": now,
            "tenant_id": str(context.tenant_id),
            "user_id": str(context.user_id),
            "roles": list(context.roles),
            "permissions": list(context.permissions),
            "enabled_services": list(context.enabled_services),
        }

        encoded_payload = self._encode(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        signature = hmac.new(
            self._secret,
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()

        return f"{encoded_payload}.{self._encode(signature)}"

    def verify(self, token: str) -> MCPRequestContext:
        if not isinstance(token, str) or not token:
            raise ValueError("invalid request identity token")

        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("invalid request identity token")

        encoded_payload, encoded_signature = parts
        try:
            payload_bytes = self._decode(encoded_payload)
            actual_signature = self._decode(encoded_signature)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid request identity token") from exc

        expected_signature = hmac.new(
            self._secret,
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise ValueError("invalid request identity signature")

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid request identity token") from exc

        if not isinstance(payload, dict):
            raise ValueError("invalid request identity token")
        if payload.get("aud") != self._audience:
            raise ValueError("invalid request identity audience")

        now = int(self._clock())
        exp = payload.get("exp")
        iat = payload.get("iat")
        if not isinstance(exp, int) or not isinstance(iat, int):
            raise ValueError("invalid request identity token")
        if exp <= now or iat > now:
            raise ValueError("request identity token is expired or not yet valid")

        try:
            return MCPRequestContext(
                tenant_id=UUID(payload["tenant_id"]),
                user_id=UUID(payload["user_id"]),
                roles=self._string_tuple(payload["roles"]),
                permissions=self._string_tuple(payload["permissions"]),
                enabled_services=self._string_tuple(payload["enabled_services"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid request identity token") from exc

    @staticmethod
    def _string_tuple(value: Any) -> tuple[str, ...]:
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError("expected list[str]")
        return tuple(value)

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode(value: str) -> bytes:
        padding = "=" * ((-len(value)) % 4)
        return base64.urlsafe_b64decode(value + padding)


def bind_request_context(context: MCPRequestContext) -> Token[MCPRequestContext | None]:
    return _request_context_var.set(context)


def reset_request_context(token: Token[MCPRequestContext | None]) -> None:
    _request_context_var.reset(token)


def get_request_context() -> MCPRequestContext:
    context = _request_context_var.get()
    if context is None:
        raise RuntimeError("trusted application request context is required")
    return context


def request_context_to_meta(token: str) -> dict[str, Any]:
    """Build MCP request metadata; identity is never a tool argument."""
    return {REQUEST_CONTEXT_META_KEY: token}


def authenticate_mcp_request(
    ctx: ServerRequestContext[Any, Any],
    signer: RequestContextSigner,
) -> MCPRequestContext:
    """Authenticate identity carried in MCP request metadata.

    Authentication failures are protocol-level request failures, so they use
    MCPError. This prevents the SDK from converting them into a generic tool
    execution failure/internal error.
    """

    meta = ctx.meta
    if meta is None:
        raise MCPError(
            -32001,
            "trusted application request context is required",
            None,
        )

    token = meta.get(REQUEST_CONTEXT_META_KEY)
    if not isinstance(token, str):
        raise MCPError(
            -32001,
            "trusted application request context is required",
            None,
        )

    try:
        return signer.verify(token)
    except ValueError as exc:
        raise MCPError(-32001, str(exc), None) from exc


async def request_identity_middleware(
    ctx: ServerRequestContext[Any, Any],
    call_next: Callable[[ServerRequestContext[Any, Any]], Awaitable[Any]],
    *,
    signer: RequestContextSigner,
    protected_methods: frozenset[str] = frozenset({"tools/call"}),
) -> Any:
    """Bind verified application identity for one inbound MCP request."""

    if ctx.method not in protected_methods:
        return await call_next(ctx)

    authenticated = authenticate_mcp_request(ctx, signer)
    token = bind_request_context(authenticated)
    try:
        return await call_next(ctx)
    finally:
        reset_request_context(token)
