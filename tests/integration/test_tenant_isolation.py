from sqlalchemy.orm import Session

from app.common.db.session import SessionLocal
from app.tenants.repository import TenantRepository
from app.tenants.scoped_repository import TenantScopedRepository


def main() -> None:
    db: Session = SessionLocal()

    try:
        tenant_repository = TenantRepository(db)

        tenant_a = tenant_repository.create(
            name="Tenant C",
            slug="tenant-c",
        )

        tenant_b = tenant_repository.create(
            name="Tenant D",
            slug="tenant-d",
        )

        print(f"Tenant A: {tenant_a.id}")
        print(f"Tenant B: {tenant_b.id}")

        tenant_a_repository = TenantScopedRepository(
            db,
            tenant_a.id,
        )

        tenant_b_repository = TenantScopedRepository(
            db,
            tenant_b.id,
        )
        

        tenant_a_result = (
            tenant_a_repository.get_current_tenant()
        )

        tenant_b_result = (
            tenant_b_repository.get_current_tenant()
        )

        assert tenant_a_result is not None
        assert tenant_b_result is not None

        assert tenant_a_result.id == tenant_a.id
        assert tenant_b_result.id == tenant_b.id

        assert tenant_a_result.id != tenant_b_result.id

        print("Tenant isolation test: PASSED")


        cross_tenant_result = tenant_a_repository.get_tenant(
            tenant_b.id,
        )

        assert cross_tenant_result is None

        print("Cross-tenant access test: PASSED")

    finally:
        db.close()


if __name__ == "__main__":
    main()