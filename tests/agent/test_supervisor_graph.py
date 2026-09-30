from __future__ import annotations

import pytest

from app.agents.specialists import SpecialistAgent
from app.agents.supervisor.graph import SupervisorAgent


class RecordingContractAgent(SpecialistAgent):
    def __init__(self) -> None:
        self.questions: list[str] = []

    @property
    def name(self) -> str:
        return "contract"

    def run(self, question: str) -> str:
        self.questions.append(question)
        return "contract-result"


class RecordingSecurityAgent(SpecialistAgent):
    def __init__(self) -> None:
        self.questions: list[str] = []

    @property
    def name(self) -> str:
        return "security"

    def run(self, question: str) -> str:
        self.questions.append(question)
        return "security-result"


class RecordingPolicyAgent(SpecialistAgent):
    def __init__(self) -> None:
        self.questions: list[str] = []

    @property
    def name(self) -> str:
        return "policy"

    def run(self, question: str) -> str:
        self.questions.append(question)
        return "policy-result"

    
def test_supervisor_routes_to_contract_agent() -> None:
    supervisor = SupervisorAgent()

    result = supervisor.run(
        "Review the vendor contract termination clause."
    )

    assert result["route"] == "contract"
    assert result["result"] == "contract_agent"

    assert result["events"] == (
        {
            "event_type": "supervisor_route",
            "route": "contract",
        },
        {
            "event_type": "agent_selected",
            "agent": "contract",
        },
    )


def test_supervisor_routes_to_security_agent() -> None:
    supervisor = SupervisorAgent()

    result = supervisor.run(
        "Check the user's access control permissions."
    )

    assert result["route"] == "security"
    assert result["result"] == "security_agent"

    assert result["events"] == (
        {
            "event_type": "supervisor_route",
            "route": "security",
        },
        {
            "event_type": "agent_selected",
            "agent": "security",
        },
    )


def test_supervisor_routes_to_policy_agent() -> None:
    supervisor = SupervisorAgent()

    result = supervisor.run(
        "Does this process comply with company policy?"
    )

    assert result["route"] == "policy"
    assert result["result"] == "policy_agent"

    assert result["events"] == (
        {
            "event_type": "supervisor_route",
            "route": "policy",
        },
        {
            "event_type": "agent_selected",
            "agent": "policy",
        },
    )


def test_supervisor_rejects_empty_question() -> None:
    supervisor = SupervisorAgent()

    with pytest.raises(ValueError):
        supervisor.run("")


def test_supervisor_rejects_unroutable_question() -> None:
    supervisor = SupervisorAgent()

    with pytest.raises(ValueError):
        supervisor.run(
            "What is the weather today?"
        )

def test_contract_route_calls_only_contract_agent() -> None:
    contract_agent = RecordingContractAgent()
    security_agent = RecordingSecurityAgent()
    policy_agent = RecordingPolicyAgent()

    supervisor = SupervisorAgent(
        contract_agent=contract_agent,
        security_agent=security_agent,
        policy_agent=policy_agent,
    )

    question = (
        "Review the vendor contract termination clause."
    )

    result = supervisor.run(question)

    assert result["route"] == "contract"
    assert result["result"] == "contract-result"

    assert contract_agent.questions == [question]
    assert security_agent.questions == []
    assert policy_agent.questions == []

def test_security_route_calls_only_security_agent() -> None:
    contract_agent = RecordingContractAgent()
    security_agent = RecordingSecurityAgent()
    policy_agent = RecordingPolicyAgent()

    supervisor = SupervisorAgent(
        contract_agent=contract_agent,
        security_agent=security_agent,
        policy_agent=policy_agent,
    )

    question = (
        "Check the user's access control permissions."
    )

    result = supervisor.run(question)

    assert result["route"] == "security"
    assert result["result"] == "security-result"

    assert contract_agent.questions == []
    assert security_agent.questions == [question]
    assert policy_agent.questions == []

def test_policy_route_calls_only_policy_agent() -> None:
    contract_agent = RecordingContractAgent()
    security_agent = RecordingSecurityAgent()
    policy_agent = RecordingPolicyAgent()

    supervisor = SupervisorAgent(
        contract_agent=contract_agent,
        security_agent=security_agent,
        policy_agent=policy_agent,
    )

    question = (
        "Does this process comply with company policy?"
    )

    result = supervisor.run(question)

    assert result["route"] == "policy"
    assert result["result"] == "policy-result"

    assert contract_agent.questions == []
    assert security_agent.questions == []
    assert policy_agent.questions == [question]

def test_supervisor_records_route_and_selected_agent() -> None:
    supervisor = SupervisorAgent()

    result = supervisor.run(
        "Review the vendor contract."
    )

    assert result["events"] == (
        {
            "event_type": "supervisor_route",
            "route": "contract",
        },
        {
            "event_type": "agent_selected",
            "agent": "contract",
        },
    )