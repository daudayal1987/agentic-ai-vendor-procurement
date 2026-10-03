from typing import Protocol
from uuid import UUID, uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from typing_extensions import TypedDict


class ApprovalAuthorizer(Protocol):
    def can_approve(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> bool:
        ...

    def can_execute(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> bool:
        ...


class FakeApprovalAuthorizationService:
    def __init__(
        self,
        authorized_approvers: set[str],
        authorized_requesters: set[str] | None = None,
    ) -> None:
        self.authorized_approvers = authorized_approvers
        self.authorized_requesters = (
            authorized_requesters
            if authorized_requesters is not None
            else set()
        )

    def can_approve(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> bool:
        return str(user_id) in self.authorized_approvers

    def can_execute(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> bool:
        return str(user_id) in self.authorized_requesters


class State(TypedDict):
    status: str
    tenant_id: str
    requester_id: str
    approval_id: str
    approval_decision: dict
    approver_id: str
    approval: bool


def validate_approval_decision(state: State) -> State:
    decision = state.get("approval_decision")

    if not isinstance(decision, dict):
        return {
            **state,
            "status": "invalid_approval",
        }

    if not isinstance(decision.get("approver_id"), str):
        return {
            **state,
            "status": "invalid_approval",
        }

    if not isinstance(decision.get("approved"), bool):
        return {
            **state,
            "status": "invalid_approval",
        }

    return {
        **state,
        "approver_id": decision["approver_id"],
        "approval": decision["approved"],
        "status": "approved",
    }


def route_after_authorization(state: State) -> str:
    if state["status"] == "unauthorized":
        return "end"

    return "sensitive_action"


def execute_sensitive_action(state: State) -> State:
    if state["status"] != "pending":
        return state

    return {
        **state,
        "status": "executed",
    }


def sensitive_action(state: State) -> State:
    decision = interrupt(
        {
            "type": "approval_required",
            "message": "Approve this sensitive action?",
            "tenant_id": state["tenant_id"],
            "requester_id": state["requester_id"],
            "approval_id": state["approval_id"],
        }
    )

    return {
        **state,
        "approval_decision": decision,
    }


def build_graph(
    approval_service: ApprovalAuthorizer,
):
    builder = StateGraph(State)

    def authorize(state: State) -> State:
        try:
            tenant_id = UUID(state["tenant_id"])
            requester_id = UUID(state["requester_id"])
        except (ValueError, TypeError):
            return {
                **state,
                "status": "unauthorized",
            }

        if not approval_service.can_execute(
            tenant_id=tenant_id,
            user_id=requester_id,
        ):
            return {
                **state,
                "status": "unauthorized",
            }

        return state

    def validate_approver(state: State) -> State:
        try:
            tenant_id = UUID(state["tenant_id"])
            approver_id = UUID(state["approver_id"])
        except (ValueError, TypeError):
            return {
                **state,
                "status": "approver_unauthorized",
            }

        if not approval_service.can_approve(
            tenant_id=tenant_id,
            user_id=approver_id,
        ):
            return {
                **state,
                "status": "approver_unauthorized",
            }

        if not state["approval"]:
            return {
                **state,
                "status": "rejected",
            }

        return {
            **state,
            "status": "pending",
        }

    def revalidate_requester(state: State) -> State:
        try:
            tenant_id = UUID(state["tenant_id"])
            requester_id = UUID(state["requester_id"])
        except (ValueError, TypeError):
            return {
                **state,
                "status": "requester_unauthorized_after_approval",
            }

        if not approval_service.can_execute(
            tenant_id=tenant_id,
            user_id=requester_id,
        ):
            return {
                **state,
                "status": "requester_unauthorized_after_approval",
            }

        return state

    builder.add_node(
        "authorize",
        authorize,
    )

    builder.add_node(
        "sensitive_action",
        sensitive_action,
    )

    builder.add_node(
        "validate_approval",
        validate_approval_decision,
    )

    builder.add_node(
        "validate_approver",
        validate_approver,
    )

    builder.add_node(
        "revalidate_requester",
        revalidate_requester,
    )

    builder.add_node(
        "execute",
        execute_sensitive_action,
    )

    builder.add_edge(
        START,
        "authorize",
    )

    builder.add_conditional_edges(
        "authorize",
        route_after_authorization,
        {
            "end": END,
            "sensitive_action": "sensitive_action",
        },
    )

    builder.add_edge(
        "sensitive_action",
        "validate_approval",
    )

    builder.add_conditional_edges(
        "validate_approval",
        lambda state: (
            "validate_approver"
            if state["status"] == "approved"
            else "end"
        ),
        {
            "validate_approver": "validate_approver",
            "end": END,
        },
    )

    builder.add_conditional_edges(
        "validate_approver",
        lambda state: (
            "revalidate_requester"
            if state["status"] == "pending"
            else "end"
        ),
        {
            "revalidate_requester": "revalidate_requester",
            "end": END,
        },
    )

    builder.add_conditional_edges(
        "revalidate_requester",
        lambda state: (
            "execute"
            if state["status"] == "pending"
            else "end"
        ),
        {
            "execute": "execute",
            "end": END,
        },
    )

    builder.add_edge(
        "execute",
        END,
    )

    return builder.compile(
        checkpointer=MemorySaver(),
    )


def make_state(
    tenant_id: str,
    requester_id: str,
) -> State:
    return {
        "status": "pending",
        "tenant_id": tenant_id,
        "requester_id": requester_id,
        "approval_id": str(uuid4()),
        "approval_decision": {},
        "approver_id": "",
        "approval": False,
    }


def test_sensitive_action_pauses_for_human_approval():
    tenant_id = str(uuid4())
    requester_id = str(uuid4())

    approval_service = FakeApprovalAuthorizationService(
        authorized_approvers=set(),
        authorized_requesters={requester_id},
    )

    graph = build_graph(
        approval_service,
    )

    config = {
        "configurable": {
            "thread_id": "hitl-test-1",
        }
    }

    result = graph.invoke(
        make_state(
            tenant_id=tenant_id,
            requester_id=requester_id,
        ),
        config=config,
    )

    assert result["__interrupt__"][0].value == {
        "type": "approval_required",
        "message": "Approve this sensitive action?",
        "tenant_id": tenant_id,
        "requester_id": requester_id,
        "approval_id": result["__interrupt__"][0].value["approval_id"],
    }


def test_sensitive_action_resumes_after_human_approval():
    tenant_id = str(uuid4())
    requester_id = str(uuid4())
    approver_id = str(uuid4())

    approval_service = FakeApprovalAuthorizationService(
        authorized_approvers={approver_id},
        authorized_requesters={requester_id},
    )

    graph = build_graph(
        approval_service,
    )

    config = {
        "configurable": {
            "thread_id": "hitl-test-2",
        }
    }

    result = graph.invoke(
        make_state(
            tenant_id=tenant_id,
            requester_id=requester_id,
        ),
        config=config,
    )

    assert result["__interrupt__"][0].value["type"] == (
        "approval_required"
    )

    result = graph.invoke(
        Command(
            resume={
                "approver_id": approver_id,
                "approved": True,
            }
        ),
        config=config,
    )

    assert result["status"] == "executed"


def test_sensitive_action_stops_after_human_rejection():
    tenant_id = str(uuid4())
    requester_id = str(uuid4())
    approver_id = str(uuid4())

    approval_service = FakeApprovalAuthorizationService(
        authorized_approvers={approver_id},
        authorized_requesters={requester_id},
    )

    graph = build_graph(
        approval_service,
    )

    config = {
        "configurable": {
            "thread_id": "hitl-test-3",
        }
    }

    result = graph.invoke(
        make_state(
            tenant_id=tenant_id,
            requester_id=requester_id,
        ),
        config=config,
    )

    assert result["__interrupt__"][0].value["type"] == (
        "approval_required"
    )

    result = graph.invoke(
        Command(
            resume={
                "approver_id": approver_id,
                "approved": False,
            }
        ),
        config=config,
    )

    assert result["status"] == "rejected"


def test_unauthorized_request_does_not_reach_hitl():
    tenant_id = str(uuid4())
    requester_id = str(uuid4())

    approval_service = FakeApprovalAuthorizationService(
        authorized_approvers=set(),
        authorized_requesters=set(),
    )

    graph = build_graph(
        approval_service,
    )

    config = {
        "configurable": {
            "thread_id": "hitl-test-4",
        }
    }

    result = graph.invoke(
        make_state(
            tenant_id=tenant_id,
            requester_id=requester_id,
        ),
        config=config,
    )

    assert result["status"] == "unauthorized"
    assert "__interrupt__" not in result


def test_unauthorized_approver_cannot_approve():
    tenant_id = str(uuid4())
    requester_id = str(uuid4())
    approver_id = str(uuid4())

    approval_service = FakeApprovalAuthorizationService(
        authorized_approvers=set(),
        authorized_requesters={requester_id},
    )

    graph = build_graph(
        approval_service,
    )

    config = {
        "configurable": {
            "thread_id": "hitl-test-5",
        }
    }

    result = graph.invoke(
        make_state(
            tenant_id=tenant_id,
            requester_id=requester_id,
        ),
        config=config,
    )

    assert result["__interrupt__"][0].value["type"] == (
        "approval_required"
    )

    result = graph.invoke(
        Command(
            resume={
                "approver_id": approver_id,
                "approved": True,
            }
        ),
        config=config,
    )

    assert result["status"] == "approver_unauthorized"


def test_requester_permission_revoked_after_approval_blocks_execution():
    tenant_id = str(uuid4())
    requester_id = str(uuid4())
    approver_id = str(uuid4())

    approval_service = FakeApprovalAuthorizationService(
        authorized_approvers={approver_id},
        authorized_requesters={requester_id},
    )

    graph = build_graph(
        approval_service,
    )

    config = {
        "configurable": {
            "thread_id": "hitl-test-6",
        }
    }

    result = graph.invoke(
        make_state(
            tenant_id=tenant_id,
            requester_id=requester_id,
        ),
        config=config,
    )

    assert result["__interrupt__"][0].value["type"] == (
        "approval_required"
    )

    approval_service.authorized_requesters.remove(
        requester_id
    )

    result = graph.invoke(
        Command(
            resume={
                "approver_id": approver_id,
                "approved": True,
            }
        ),
        config=config,
    )

    assert result["status"] == (
        "requester_unauthorized_after_approval"
    )


def test_invalid_approval_payload_is_rejected():
    tenant_id = str(uuid4())
    requester_id = str(uuid4())

    approval_service = FakeApprovalAuthorizationService(
        authorized_approvers=set(),
        authorized_requesters={requester_id},
    )

    graph = build_graph(
        approval_service,
    )

    config = {
        "configurable": {
            "thread_id": "hitl-test-invalid-1",
        }
    }

    result = graph.invoke(
        make_state(
            tenant_id=tenant_id,
            requester_id=requester_id,
        ),
        config=config,
    )

    assert result["__interrupt__"][0].value["type"] == (
        "approval_required"
    )

    result = graph.invoke(
        Command(resume={
            "approved": True
        }),
        config=config,
    )

    assert result["status"] == "invalid_approval"


def test_invalid_approval_boolean_is_rejected():
    tenant_id = str(uuid4())
    requester_id = str(uuid4())

    approval_service = FakeApprovalAuthorizationService(
        authorized_approvers=set(),
        authorized_requesters={requester_id},
    )

    graph = build_graph(
        approval_service,
    )

    config = {
        "configurable": {
            "thread_id": "hitl-test-invalid-2",
        }
    }

    graph.invoke(
        make_state(
            tenant_id=tenant_id,
            requester_id=requester_id,
        ),
        config=config,
    )

    result = graph.invoke(
        Command(
            resume={
                "approver_id": str(uuid4()),
                "approved": "yes",
            }
        ),
        config=config,
    )

    assert result["status"] == "invalid_approval"


def test_invalid_approver_id_is_rejected():
    tenant_id = str(uuid4())
    requester_id = str(uuid4())

    approval_service = FakeApprovalAuthorizationService(
        authorized_approvers=set(),
        authorized_requesters={requester_id},
    )

    graph = build_graph(
        approval_service,
    )

    config = {
        "configurable": {
            "thread_id": "hitl-test-invalid-3",
        }
    }

    graph.invoke(
        make_state(
            tenant_id=tenant_id,
            requester_id=requester_id,
        ),
        config=config,
    )

    result = graph.invoke(
        Command(
            resume={
                "approver_id": 123,
                "approved": True,
            }
        ),
        config=config,
    )

    assert result["status"] == "invalid_approval"
