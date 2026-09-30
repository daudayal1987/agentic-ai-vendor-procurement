from __future__ import annotations

import pytest

from app.agents.specialists.contract import ContractAgent 
from app.agents.specialists.policy import PolicyAgent
from app.agents.specialists.security import SecurityAgent


def test_contract_agent() -> None:
    agent = ContractAgent()

    assert agent.name == "contract"
    assert (
        agent.run("Review the contract.")
        == "contract_agent"
    )


def test_security_agent() -> None:
    agent = SecurityAgent()

    assert agent.name == "security"
    assert (
        agent.run("Check access control.")
        == "security_agent"
    )


def test_policy_agent() -> None:
    agent = PolicyAgent()

    assert agent.name == "policy"
    assert (
        agent.run("Check company policy.")
        == "policy_agent"
    )


@pytest.mark.parametrize(
    "agent_class",
    [
        ContractAgent,
        SecurityAgent,
        PolicyAgent,
    ],
)
def test_specialists_reject_empty_questions(
    agent_class,
) -> None:
    agent = agent_class()

    with pytest.raises(ValueError):
        agent.run("")