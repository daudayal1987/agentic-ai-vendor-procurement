from __future__ import annotations

import pytest

from app.agents.supervisor.router import SupervisorRouter


def test_routes_contract_request() -> None:
    router = SupervisorRouter()

    route = router.route(
        "Review the vendor contract termination clause."
    )

    assert route == "contract"


def test_routes_security_request() -> None:
    router = SupervisorRouter()

    route = router.route(
        "Check whether this user has permission "
        "to access the document."
    )

    assert route == "security"


def test_routes_policy_request() -> None:
    router = SupervisorRouter()

    route = router.route(
        "Does this process comply with company policy?"
    )

    assert route == "policy"


def test_routing_is_case_insensitive() -> None:
    router = SupervisorRouter()

    route = router.route(
        "Review the CONTRACT termination clause."
    )

    assert route == "contract"


def test_empty_question_is_rejected() -> None:
    router = SupervisorRouter()

    with pytest.raises(ValueError):
        router.route("")


def test_unrecognized_question_is_rejected() -> None:
    router = SupervisorRouter()

    with pytest.raises(ValueError):
        router.route(
            "What is the weather today?"
        )


def test_ambiguous_question_is_rejected() -> None:
    router = SupervisorRouter()

    with pytest.raises(ValueError):
        router.route(
            "Check the security requirements "
            "in the contract policy."
        )