from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    REVIEWER = "reviewer"


class Permission(StrEnum):
    TENANT_READ = "tenant:read"
    TENANT_MANAGE = "tenant:manage"

    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"

    ANALYSIS_RUN = "analysis:run"

    APPROVAL_REVIEW = "approval:review"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(
        {
            Permission.TENANT_READ,
            Permission.TENANT_MANAGE,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_WRITE,
            Permission.ANALYSIS_RUN,
            Permission.APPROVAL_REVIEW,
        }
    ),
    Role.ANALYST: frozenset(
        {
            Permission.TENANT_READ,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_WRITE,
            Permission.ANALYSIS_RUN,
        }
    ),
    Role.REVIEWER: frozenset(
        {
            Permission.TENANT_READ,
            Permission.DOCUMENT_READ,
            Permission.APPROVAL_REVIEW,
        }
    ),
}


def has_permission(
    role: Role,
    permission: Permission,
) -> bool:
    return permission in ROLE_PERMISSIONS.get(
        role,
        frozenset(),
    )