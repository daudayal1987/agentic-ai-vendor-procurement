from __future__ import annotations

from langchain_ollama import ChatOllama

from app.agents.langgraph_react import (
    LangGraphReActAgent,
)
from day15_tool_calling import (
    MODEL_NAME,
    build_tool,
)


MAX_ITERATIONS = 5


def main() -> None:
    tool, tenant_context = build_tool()

    llm = ChatOllama(
        model=MODEL_NAME,
        temperature=0,
    )

    agent = LangGraphReActAgent(
        model=llm,
        tools=[tool],
        max_iterations=MAX_ITERATIONS,
    )

    question = (
        "Determine the vendor termination notice "
        "period. Use the enterprise document search "
        "tool when needed. Answer only from the "
        "retrieved evidence."
    )

    result = agent.run(
        question
    )

    print(
        "\n=============================="
    )
    print(
        "DAY 17 — LANGGRAPH"
    )
    print(
        "=============================="
    )

    print(
        f"\nTenant: {tenant_context.tenant_id}"
    )

    print(
        f"Iterations: {result['iterations']}"
    )

    print(
        "\n=== GRAPH EVENTS ==="
    )

    for event in result["events"]:
        event_type = event["event_type"]

        if event_type == "tool_call":
            print(
                f"[iteration={event['iteration']}] "
                f"TOOL CALL → {event['tool_name']}"
            )

        elif event_type == "tool_result":
            print(
                f"[iteration={event['iteration']}] "
                f"TOOL RESULT ← {event['tool_name']}"
            )

        elif event_type == "tool_error":
            print(
                f"[iteration={event['iteration']}] "
                f"TOOL ERROR ← {event['tool_name']}"
            )

        elif event_type == "agent_finish":
            print(
                f"[iteration={event['iteration']}] "
                "AGENT FINISH"
            )

    print(
        "\n=== FINAL ANSWER ==="
    )

    print(
        result["answer"]
    )


if __name__ == "__main__":
    main()