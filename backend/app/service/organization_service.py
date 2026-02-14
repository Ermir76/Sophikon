"""
Organization business logic.

Handles listing, creating, updating, and soft-deleting organizations.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.schema.organization import OrganizationCreate, OrganizationUpdate


async def list_organizations(
    db: AsyncSession,
    user: User,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Organization], int]:
    """
    List organizations the user is a member of.

    Returns (organizations, total_count).
    """
    base_query = (
        select(Organization)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .where(
            Organization.is_deleted.is_(False),
            OrganizationMember.user_id == user.id,
        )
    )

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * per_page
    paginated_query = (
        base_query.order_by(Organization.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )

    result = await db.execute(paginated_query)
    organizations = list(result.scalars().all())

    return organizations, total


async def create_organization(
    db: AsyncSession,
    user: User,
    data: OrganizationCreate,
) -> Organization:
    """Create a new organization and make the user the owner."""
    # Check slug uniqueness
    existing = await db.execute(
        select(Organization).where(
            Organization.slug == data.slug,
            Organization.is_deleted.is_(False),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Organization with this slug already exists",
        )

    return await _create_org_internal(db, user, data.name, data.slug, is_personal=False)


async def create_personal_organization(
    db: AsyncSession,
    user: User,
) -> Organization:
    """
    Create a personal organization for a user.
    Slug is derived from email username, ensuring uniqueness.
    """
    # Derive base slug from email (e.g., "john.doe" from "john.doe@example.com")
    base_slug = user.email.split("@")[0].lower()
    # Remove non-alphanumeric chars (keep hyphens/underscores)
    base_slug = "".join(c for c in base_slug if c.isalnum() or c in "-_")
    if not base_slug:
        base_slug = "user"

    # Ensure uniqueness
    slug = base_slug
    counter = 1
    while True:
        existing = await db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    org_name = f"{user.full_name}'s Org"
    return await _create_org_internal(db, user, org_name, slug, is_personal=True)


async def _create_org_internal(
    db: AsyncSession,
    user: User,
    name: str,
    slug: str,
    is_personal: bool,
) -> Organization:
    """Internal helper to create org + owner member."""
    org = Organization(
        name=name,
        slug=slug,
        is_personal=is_personal,
    )
    db.add(org)
    await db.flush()  # Get org.id

    # Make the creator the owner
    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="owner",
    )
    db.add(member)

    await db.commit()
    await db.refresh(org)
    return org


async def get_organization_by_id(
    db: AsyncSession,
    org_id: UUID,
) -> Organization | None:
    """Get an organization by ID (excludes deleted)."""
    result = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def update_organization(
    db: AsyncSession,
    org: Organization,
    data: OrganizationUpdate,
) -> Organization:
    """Update an organization with partial data."""
    update_data = data.model_dump(exclude_unset=True)

    # If slug is being changed, check uniqueness
    if "slug" in update_data:
        existing = await db.execute(
            select(Organization).where(
                Organization.slug == update_data["slug"],
                Organization.id != org.id,
                Organization.is_deleted.is_(False),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Organization with this slug already exists",
            )

    for field, value in update_data.items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)
    return org


async def soft_delete_organization(
    db: AsyncSession,
    org: Organization,
) -> None:
    """Soft delete an organization."""
    if org.is_personal:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete personal organization",
        )
    org.is_deleted = True
    org.deleted_at = datetime.now(timezone.utc)
    await db.commit()
