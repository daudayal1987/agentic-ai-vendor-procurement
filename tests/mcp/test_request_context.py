from __future__ import annotations

import asyncio
from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from mcp import MCPError
from mcp.server import ServerRequestContext

from app.mcp.request_context import (
    REQUEST_CONTEXT_META_KEY,
    MCPRequestContext,
    RequestContextSigner,
    bind_request_context,
    get_request_context,
    request_context_to_meta,
    request_identity_middleware,
    reset_request_context,
)

SECRET = b"test-mcp-secret"
TENANT_A = UUID("11111111-1111-1111-1111-111111111111")
TENANT_B = UUID("22222222-2222-2222-2222-222222222222")


def make_context(tenant_id: UUID = TENANT_A) -> MCPRequestContext:
    return MCPRequestContext(
        tenant_id=tenant_id,
        user_id=uuid4(),
        roles=("ANALYST",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )


def make_server_request_context(*, meta=None, method="tools/call"):
    return ServerRequestContext(
        session=object(),
        lifespan_context=None,
        protocol_version="2026-07-28",
        method=method,
        meta=meta,
        request_id="1",
    )


def test_issue_and_verify_round_trip() -> None:
    signer = RequestContextSigner(SECRET, clock=lambda: 1000)
    context = make_context()

    token = signer.issue(context)
    verified = signer.verify(token)

    assert verified == context


def test_tampering_is_rejected() -> None:
    signer = RequestContextSigner(SECRET, clock=lambda: 1000)
    token = signer.issue(make_context(TENANT_A))
    payload, signature = token.split(".")

    tampered = replace(make_context(TENANT_B))
    assert tampered.tenant_id == TENANT_B

    import base64
    import json

    padding = "=" * ((-len(payload)) % 4)
    data = json.loads(base64.urlsafe_b64decode(payload + padding))
    data["tenant_id"] = str(TENANT_B)
    new_payload = base64.urlsafe_b64encode(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()

    with pytest.raises(ValueError, match="signature"):
        signer.verify(f"{new_payload}.{signature}")


def test_expired_token_is_rejected() -> None:
    issue_signer = RequestContextSigner(SECRET, ttl_seconds=10, clock=lambda: 1000)
    verify_signer = RequestContextSigner(SECRET, ttl_seconds=10, clock=lambda: 1010)

    token = issue_signer.issue(make_context())

    with pytest.raises(ValueError, match="expired"):
        verify_signer.verify(token)


def test_wrong_audience_is_rejected() -> None:
    signer = RequestContextSigner(SECRET, audience="server-a", clock=lambda: 1000)
    verifier = RequestContextSigner(SECRET, audience="server-b", clock=lambda: 1000)

    token = signer.issue(make_context())

    with pytest.raises(ValueError, match="audience"):
        verifier.verify(token)


def test_meta_contains_identity_but_not_tool_arguments() -> None:
    signer = RequestContextSigner(SECRET, clock=lambda: 1000)
    token = signer.issue(make_context())

    meta = request_context_to_meta(token)

    assert REQUEST_CONTEXT_META_KEY in meta
    assert "tenant_id" not in meta


def test_context_var_is_task_local() -> None:
    async def worker(context: MCPRequestContext) -> UUID:
        token = bind_request_context(context)
        try:
            await asyncio.sleep(0)
            return get_request_context().tenant_id
        finally:
            reset_request_context(token)

    async def run() -> list[UUID]:
        return await asyncio.gather(
            worker(make_context(TENANT_A)),
            worker(make_context(TENANT_B)),
        )

    assert asyncio.run(run()) == [TENANT_A, TENANT_B]


def test_get_request_context_requires_binding() -> None:
    with pytest.raises(RuntimeError, match="trusted application request context"):
        get_request_context()


@pytest.mark.anyio
async def test_middleware_binds_and_resets_identity() -> None:
    signer = RequestContextSigner(SECRET, clock=lambda: 1000)
    context = make_context(TENANT_A)
    token = signer.issue(context)
    ctx = make_server_request_context(meta=request_context_to_meta(token))

    observed: list[UUID] = []

    async def call_next(_ctx):
        observed.append(get_request_context().tenant_id)
        return "ok"

    assert await request_identity_middleware(ctx, call_next, signer=signer) == "ok"
    assert observed == [TENANT_A]

    with pytest.raises(RuntimeError, match="trusted application request context"):
        get_request_context()


@pytest.mark.anyio
async def test_middleware_resets_identity_after_handler_failure() -> None:
    signer = RequestContextSigner(SECRET, clock=lambda: 1000)
    token = signer.issue(make_context(TENANT_A))
    ctx = make_server_request_context(meta=request_context_to_meta(token))

    async def call_next(_ctx):
        assert get_request_context().tenant_id == TENANT_A
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await request_identity_middleware(ctx, call_next, signer=signer)

    with pytest.raises(RuntimeError, match="trusted application request context"):
        get_request_context()


@pytest.mark.anyio
async def test_missing_identity_is_protocol_error() -> None:
    signer = RequestContextSigner(SECRET)
    ctx = make_server_request_context(meta=None)

    async def call_next(_ctx):
        raise AssertionError("handler must not run")

    with pytest.raises(MCPError, match="trusted application request context"):
        await request_identity_middleware(ctx, call_next, signer=signer)


@pytest.mark.anyio
async def test_invalid_signature_is_protocol_error() -> None:
    signer = RequestContextSigner(SECRET, clock=lambda: 1000)
    token = signer.issue(make_context())
    payload, signature = token.split(".")
    bad_signature = ("A" if signature[0] != "A" else "B") + signature[1:]
    ctx = make_server_request_context(
        meta=request_context_to_meta(f"{payload}.{bad_signature}")
    )

    async def call_next(_ctx):
        raise AssertionError("handler must not run")

    with pytest.raises(MCPError, match="signature"):
        await request_identity_middleware(ctx, call_next, signer=signer)
