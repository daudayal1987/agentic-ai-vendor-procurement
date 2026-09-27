from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import get_current_principal
from app.auth.principal import AuthenticatedPrincipal
from app.documents.dependencies import get_document_service
from app.documents.schemas import DocumentResponse
from app.documents.service import DocumentService
from app.tenants.dependencies import get_tenant_context
from app.tenants.context import TenantContext
from app.auth.authorization import require_permission
from app.policies.rbac import Permission


from app.common.logging import get_logger   
logger = get_logger("http")

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    tenant_context: TenantContext = Depends(require_permission(Permission.DOCUMENT_WRITE)),
    document_service: DocumentService = Depends(get_document_service),
):

    content = await file.read()
    logger.info(f"Content read from file: {len(content)} bytes, filename: {file.filename}, content_type: {file.content_type}")
    logger.info(f"Content preview (first 100 bytes): {content[:100]}")  # Log the first 100 bytes of content for debugging

    try:
        document = document_service.upload_document(
            tenant_id=tenant_context.tenant_id,
            filename=file.filename or "unnamed",
            content_type=file.content_type or "",
            content=content,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return document


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: UUID,
    tenant_context: TenantContext = Depends(require_permission(Permission.DOCUMENT_READ)),
    document_service: DocumentService = Depends(get_document_service),
):
    document = document_service.get_document(
        tenant_id=tenant_context.tenant_id,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    tenant_context: TenantContext = Depends(require_permission(Permission.DOCUMENT_LIST)),
    document_service: DocumentService = Depends(
        get_document_service
    ),
):
    return document_service.list_documents(
        tenant_id=tenant_context.tenant_id,
    )