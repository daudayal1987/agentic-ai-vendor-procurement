# from __future__ import annotations

# from uuid import UUID, uuid4

# from langchain_core.messages import HumanMessage, ToolMessage
# from langchain_ollama import ChatOllama
# from pydantic import BaseModel, Field

# from app.retrieval.config import RetrievalConfig
# from app.retrieval.dense import DenseRetriever
# from app.retrieval.embeddings.dependencies import get_embedding_model
# from app.retrieval.models import RetrievedChunk
# from app.retrieval.vector_store.faiss_index import FaissVectorIndex
# from app.retrieval.vector_store.models import IndexedChunk
# from app.tenants.context import TenantContext
# from app.tools.search_documents import create_search_documents_tool


# MODEL_NAME = "qwen3:1.7b"


# class EvidenceAnswer(BaseModel):
#     """Structured final answer generated from retrieved evidence."""

#     answer: str = Field(
#         description="Concise answer grounded in retrieved evidence."
#     )
#     evidence: list[str] = Field(
#         description="Evidence statements supporting the answer."
#     )
#     missing_information: list[str] = Field(
#         description="Important information that could not be established.",
#     )
#     requires_human_review: bool = Field(
#         description="Whether human review is required."
#     )


# def build_demo_chunks(
#     tenant_a: UUID,
#     tenant_b: UUID,
# ) -> list[IndexedChunk]:
#     """Create a tiny deterministic enterprise-document corpus."""

#     return [
#         IndexedChunk(
#             vector_id=0,
#             chunk_id=uuid4(),
#             document_id=uuid4(),
#             tenant_id=tenant_a,
#             text=(
#                 "Termination: Either party may terminate the agreement "
#                 "with 30 days written notice."
#             ),
#             section="Termination",
#             position=0,
#             token_count=14,
#             source_metadata={
#                 "filename": "vendor-contract.pdf",
#                 "page": 4,
#             },
#         ),
#         IndexedChunk(
#             vector_id=1,
#             chunk_id=uuid4(),
#             document_id=uuid4(),
#             tenant_id=tenant_a,
#             text=(
#                 "SLA: The service availability commitment is 99.9% "
#                 "monthly uptime."
#             ),
#             section="SLA",
#             position=1,
#             token_count=13,
#             source_metadata={
#                 "filename": "sla.pdf",
#                 "page": 2,
#             },
#         ),
#         IndexedChunk(
#             vector_id=2,
#             chunk_id=uuid4(),
#             document_id=uuid4(),
#             tenant_id=tenant_a,
#             text=(
#                 "Security: Vendor access requires multi-factor "
#                 "authentication and quarterly access reviews."
#             ),
#             section="Security",
#             position=2,
#             token_count=14,
#             source_metadata={
#                 "filename": "security-questionnaire.pdf",
#                 "page": 7,
#             },
#         ),
#         IndexedChunk(
#             vector_id=3,
#             chunk_id=uuid4(),
#             document_id=uuid4(),
#             tenant_id=tenant_b,
#             text=(
#                 "Tenant B confidential contract: termination requires "
#                 "90 days written notice."
#             ),
#             section="Termination",
#             position=0,
#             token_count=13,
#             source_metadata={
#                 "filename": "tenant-b-contract.pdf",
#                 "page": 3,
#             },
#         ),
#     ]


# def build_retriever(
#     indexed_chunks: list[IndexedChunk],
# ) -> DenseRetriever:
#     embedding_model = get_embedding_model()

#     vector_index = FaissVectorIndex(
#         dimension=embedding_model.dimension,
#     )

#     texts = [
#         chunk.text
#         for chunk in indexed_chunks
#     ]

#     embeddings = embedding_model.embed_documents(texts)

#     vector_ids = vector_index.add(embeddings)

#     if vector_ids != [
#         chunk.vector_id
#         for chunk in indexed_chunks
#     ]:
#         raise RuntimeError(
#             "Demo vector IDs do not match IndexedChunk IDs."
#         )

#     return DenseRetriever(
#         embedding_model=embedding_model,
#         vector_index=vector_index,
#         indexed_chunks=indexed_chunks,
#         config=RetrievalConfig(
#             default_top_k=5,
#             max_top_k=20,
#         ),
#     )


# def build_tool() -> tuple[
#     object,
#     TenantContext,
# ]:
#     tenant_a = uuid4()
#     tenant_b = uuid4()

#     tenant_context = TenantContext(
#         tenant_id=tenant_a,
#         user_id=uuid4(),
#         roles=("ANALYST",),
#         permissions=("document:read", "analysis:run"),
#     )

#     indexed_chunks = build_demo_chunks(
#         tenant_a=tenant_a,
#         tenant_b=tenant_b,
#     )

#     retriever = build_retriever(indexed_chunks)

#     tool = create_search_documents_tool(
#         retriever_factory=lambda _: retriever,
#         tenant_context=tenant_context,
#     )

#     return tool, tenant_context


# def run_tool_calling() -> None:
#     tool, tenant_context = build_tool()

#     llm = ChatOllama(
#         model=MODEL_NAME,
#         temperature=0,
#     )

#     model_with_tools = llm.bind_tools([tool])

#     messages = [
#         HumanMessage(
#             content=(
#                 "According to the enterprise documents, what is "
#                 "the vendor termination notice period? "
#                 "Use the document search tool."
#             )
#         )
#     ]

#     first_response = model_with_tools.invoke(messages)

#     print("\n=== FIRST MODEL RESPONSE ===")
#     print(first_response)

#     if not first_response.tool_calls:
#         print("\nModel did not request a tool call.")
#         print("Content:")
#         print(first_response.content)
#         return

#     messages.append(first_response)

#     for tool_call in first_response.tool_calls:
#         if tool_call["name"] != "search_documents":
#             raise RuntimeError(
#                 f"Unexpected tool: {tool_call['name']}"
#             )

#         tool_result = tool.invoke(tool_call["args"])

#         print("\n=== TOOL CALL ===")
#         print(tool_call)

#         print("\n=== TOOL RESULT ===")
#         print(tool_result)

#         messages.append(
#             ToolMessage(
#                 content=str(tool_result),
#                 tool_call_id=tool_call["id"],
#             )
#         )

#     final_response = model_with_tools.invoke(messages)

#     print("\n=== FINAL MODEL RESPONSE ===")
#     print(final_response.content)

#     print("\n=== TENANT ===")
#     print(tenant_context.tenant_id)


# def run_structured_output() -> None:
#     tool, _ = build_tool()

#     llm = ChatOllama(
#         model=MODEL_NAME,
#         temperature=0,
#     )

#     tool_enabled_model = llm.bind_tools([tool])

#     messages = [
#         HumanMessage(
#             content=(
#                 "Determine the vendor termination notice period. "
#                 "Use the document search tool and then answer "
#                 "using only the retrieved evidence."
#             )
#         )
#     ]

#     first_response = tool_enabled_model.invoke(messages)

#     if not first_response.tool_calls:
#         raise RuntimeError(
#             "Expected the model to request search_documents."
#         )

#     messages.append(first_response)

#     for tool_call in first_response.tool_calls:
#         if tool_call["name"] != "search_documents":
#             raise RuntimeError(
#                 f"Unexpected tool: {tool_call['name']}"
#             )

#         result = tool.invoke(tool_call["args"])

#         messages.append(
#             ToolMessage(
#                 content=str(result),
#                 tool_call_id=tool_call["id"],
#             )
#         )

#     structured_model = llm.with_structured_output(
#         EvidenceAnswer,
#         method="json_schema",  # Forces local Ollama engine to output exact JSON
#         include_raw=True       # Returns a dict with 'raw', 'parsed', and 'parsing_error'
#     )

#     response_dict = structured_model.invoke(
#         [
#             *messages,
#             HumanMessage(
#                 content=(
#                     "Now produce the final structured answer. "
#                     "Do not invent facts not present in the evidence."
#                 )
#             ),
#         ]
#     )

#     # 3. Handle the structured output dict dictionary format safely
#     answer = response_dict.get("parsed")
#     parsing_error = response_dict.get("parsing_error")

#     if answer is None:
#         print("\nCRITICAL: Structured output generation failed!")
#         if parsing_error:
#             print(f"Parsing Exception: {parsing_error}")
#         print(f"Raw text generated by model: {response_dict.get('raw').content}")
#         return

#     print("\n=== STRUCTURED OUTPUT ===")
#     print(answer.model_dump_json(indent=2))


# if __name__ == "__main__":
#     run_structured_output()