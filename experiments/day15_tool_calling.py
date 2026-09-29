from __future__ import annotations

from uuid import UUID, uuid4

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from app.retrieval.dense import DenseRetriever
from app.retrieval.embeddings.dependencies import get_embedding_model
from app.retrieval.models import RetrievedChunk
from app.retrieval.vector_store.faiss_index import FaissVectorIndex
from app.retrieval.vector_store.models import IndexedChunk
from app.tenants.context import TenantContext
from app.tools.search_documents import create_search_documents_tool


MODEL_NAME = "qwen3:1.7b"


class EvidenceAnswer(BaseModel):
    """Final structured answer produced by the LLM."""

    answer: str = Field(
        description="Evidence-grounded answer to the user's question."
    )

    evidence: list[str] = Field(
        description=(
            "Relevant evidence statements directly supported "
            "by retrieved enterprise documents."
        )
    )

    missing_information: list[str] = Field(
        description=(
            "Important information that is missing from the "
            "retrieved evidence."
        )
    )

    requires_human_review: bool = Field(
        description=(
            "Whether the result requires human review before "
            "being used for a consequential decision."
        )
    )


def build_demo_chunks() -> list[IndexedChunk]:
    """
    Build a small deterministic corpus for the Day 15 experiment.

    Tenant A contains the documents that should be searchable.

    Tenant B contains a different confidential contract. This is
    deliberately included to demonstrate tenant isolation.
    """

    tenant_a_id = UUID("11111111-1111-1111-1111-111111111111")
    tenant_b_id = UUID("22222222-2222-2222-2222-222222222222")

    document_a_contract = UUID(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )

    document_a_sla = UUID(
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    )

    document_a_security = UUID(
        "cccccccc-cccc-cccc-cccc-cccccccccccc"
    )

    document_b_contract = UUID(
        "dddddddd-dddd-dddd-dddd-dddddddddddd"
    )

    return [
        IndexedChunk(
            vector_id=0,
            chunk_id=uuid4(),
            document_id=document_a_contract,
            tenant_id=tenant_a_id,
            text=(
                "Termination: Either party may terminate the "
                "agreement with 30 days written notice."
            ),
            section="Termination",
            position=0,
            token_count=12,
            source_metadata={
                "filename": "vendor-contract.pdf",
                "page": 4,
            },
        ),
        IndexedChunk(
            vector_id=1,
            chunk_id=uuid4(),
            document_id=document_a_sla,
            tenant_id=tenant_a_id,
            text=(
                "Service Level Agreement: The vendor must maintain "
                "99.9% monthly service availability."
            ),
            section="SLA",
            position=0,
            token_count=13,
            source_metadata={
                "filename": "vendor-sla.pdf",
                "page": 2,
            },
        ),
        IndexedChunk(
            vector_id=2,
            chunk_id=uuid4(),
            document_id=document_a_security,
            tenant_id=tenant_a_id,
            text=(
                "Security controls require multi-factor authentication "
                "and quarterly access reviews."
            ),
            section="Security",
            position=0,
            token_count=11,
            source_metadata={
                "filename": "security-questionnaire.pdf",
                "page": 7,
            },
        ),
        IndexedChunk(
            vector_id=3,
            chunk_id=uuid4(),
            document_id=document_b_contract,
            tenant_id=tenant_b_id,
            text=(
                "Termination: Either party may terminate the agreement "
                "with 90 days written notice."
            ),
            section="Termination",
            position=0,
            token_count=13,
            source_metadata={
                "filename": "confidential-vendor-contract.pdf",
                "page": 8,
            },
        ),
    ]


def build_retriever(
    tenant_context: TenantContext,
) -> DenseRetriever:
    """
    Build the real Day 11 dense retrieval stack used by Day 15.

    The experiment uses:
        BGE-small-en-v1.5
        Sentence Transformers
        FAISS IndexFlatIP
        DenseRetriever
    """

    embedding_model = get_embedding_model()

    vector_index = FaissVectorIndex(
        dimension=embedding_model.dimension
    )

    chunks = build_demo_chunks()

    texts = [
        chunk.text
        for chunk in chunks
    ]

    embeddings = embedding_model.embed_documents(texts)

    vector_index.add(embeddings)

    return DenseRetriever(
        embedding_model=embedding_model,
        vector_index=vector_index,
        indexed_chunks=chunks,
    )


def build_tool() -> tuple[object, TenantContext]:
    """
    Build the tenant-scoped search_documents tool.

    Tenant A is used as the authenticated runtime context.
    """

    tenant_context = TenantContext(
        tenant_id=UUID(
            "11111111-1111-1111-1111-111111111111"
        ),
        user_id=None,
        roles=("ANALYST",),
        permissions=(
            "document:read",
            "analysis:run",
        ),
    )

    tool = create_search_documents_tool(
        retriever_factory=build_retriever,
        tenant_context=tenant_context,
    )

    return tool, tenant_context


def run_tool_calling() -> None:
    """
    Demonstrate the complete Day 15 tool-calling loop.

    Flow:

        User question
            ↓
        Qwen3
            ↓
        tool call
            ↓
        search_documents
            ↓
        DenseRetriever
            ↓
        FAISS
            ↓
        ToolMessage
            ↓
        Qwen3
            ↓
        grounded answer
    """

    tool, tenant_context = build_tool()

    llm = ChatOllama(
        model=MODEL_NAME,
        temperature=0,
    )

    tool_enabled_model = llm.bind_tools(
        [tool]
    )

    messages = [
        HumanMessage(
            content=(
                "Determine the vendor termination notice period. "
                "Use the document search tool and then answer "
                "using only the retrieved evidence."
            )
        )
    ]

    first_response = tool_enabled_model.invoke(
        messages
    )

    print("\n=== FIRST MODEL RESPONSE ===")
    print(first_response)

    if not first_response.tool_calls:
        raise RuntimeError(
            "Expected the model to request search_documents."
        )

    messages.append(
        first_response
    )

    print("\n=== TOOL CALL ===")

    for tool_call in first_response.tool_calls:
        if tool_call["name"] != "search_documents":
            raise RuntimeError(
                f"Unexpected tool: {tool_call['name']}"
            )

        print(tool_call)

        result = tool.invoke(
            tool_call["args"]
        )

        print("\n=== TOOL RESULT ===")
        print(result)

        messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            )
        )

    final_response = tool_enabled_model.invoke(
        messages
    )

    print("\n=== FINAL MODEL RESPONSE ===")
    print(final_response.content)

    print("\n=== TENANT CONTEXT ===")
    print(f"tenant_id={tenant_context.tenant_id}")


def run_structured_output() -> None:
    """
    Demonstrate structured final output with explicit parsing-error
    handling.

    include_raw=True gives us:
        raw
        parsed
        parsing_error

    This prevents a malformed model response from immediately
    crashing the experiment.
    """

    tool, _ = build_tool()

    llm = ChatOllama(
        model=MODEL_NAME,
        temperature=0,
    )

    tool_enabled_model = llm.bind_tools(
        [tool]
    )

    messages = [
        HumanMessage(
            content=(
                "Determine the vendor termination notice period. "
                "Use the document search tool and then answer "
                "using only the retrieved evidence."
            )
        )
    ]

    first_response = tool_enabled_model.invoke(
        messages
    )

    if not first_response.tool_calls:
        raise RuntimeError(
            "Expected the model to request search_documents."
        )

    messages.append(
        first_response
    )

    for tool_call in first_response.tool_calls:
        if tool_call["name"] != "search_documents":
            raise RuntimeError(
                f"Unexpected tool: {tool_call['name']}"
            )

        result = tool.invoke(
            tool_call["args"]
        )

        messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
            )
        )

    structured_model = llm.with_structured_output(
        EvidenceAnswer,
        method="json_schema",
        include_raw=True,
    )

    response_dict = structured_model.invoke(
        [
            *messages,
            HumanMessage(
                content=(
                    "Now produce the final structured answer. "
                    "Do not invent facts not present in the evidence."
                )
            ),
        ]
    )

    answer = response_dict.get(
        "parsed"
    )

    parsing_error = response_dict.get(
        "parsing_error"
    )

    if answer is None:
        print(
            "\nCRITICAL: Structured output generation failed!"
        )

        if parsing_error:
            print(
                f"Parsing Exception: {parsing_error}"
            )

        raw_response = response_dict.get(
            "raw"
        )

        if raw_response is not None:
            print(
                "\nRaw model response:"
            )
            print(
                raw_response.content
            )

        return

    print(
        "\n=== STRUCTURED OUTPUT ==="
    )

    print(
        answer.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    print(
        "\n=============================="
    )
    print(
        "DAY 15 — TOOL CALLING"
    )
    print(
        "=============================="
    )

    run_tool_calling()

    print(
        "\n=============================="
    )
    print(
        "DAY 15 — STRUCTURED OUTPUT"
    )
    print(
        "=============================="
    )

    run_structured_output()