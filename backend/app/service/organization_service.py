"""
Organization business logic.

Handles listing, creating, updating, and soft-deleting organizations.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError, ResourceConflictError
from app.models.organization import Organization
from app.models.user import User
from app.repository import organization_repo
from app.service.contracts.organization import (
    OrganizationCreateInput,
    OrganizationPatchInput,
)


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
    return await organization_repo.list_for_user(
        db,
        user_id=user.id,
        page=page,
        per_page=per_page,
    )


async def create_organization(
    db: AsyncSession,
    user: User,
    payload: OrganizationCreateInput,
) -> Organization:
    """Create a new organization and make the user the owner."""
    if await organization_repo.slug_exists(db, slug=payload["slug"]):
        raise ResourceConflictError("Organization with this slug already exists")

    try:
        return await _create_org_internal(
            db,
            user,
            payload["name"],
            payload["slug"],
            is_personal=False,
        )
    except IntegrityError:
        await db.rollback()
        raise ResourceConflictError("Organization with this slug already exists")


async def create_personal_organization(
    db: AsyncSession,
    user: User,
    *,
    commit: bool = True,
) -> Organization:
    """
    Create a personal organization for a user.
    Slug is derived from email username, ensuring uniqueness.
    """
    # Derive base slug from email (e.g., "john.doe" from "john.doe@example.com")
    base_slug = user.email.split("@")[0].lower()
    # Replace underscores/dots with hyphens, keep only alphanumeric + hyphens
    base_slug = base_slug.replace("_", "-").replace(".", "-")
    base_slug = "".join(c for c in base_slug if c.isalnum() or c == "-")
    while "--" in base_slug:
        base_slug = base_slug.replace("--", "-")
    base_slug = base_slug.strip("-")
    if not base_slug:
        base_slug = "user"

    # Ensure uniqueness
    slug = base_slug
    counter = 1
    while True:
        existing = await organization_repo.get_by_slug(db, slug=slug)
        if existing is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    org_name = f"{user.full_name}'s Org"
    return await _create_org_internal(
        db, user, org_name, slug, is_personal=True, commit=commit
    )


async def _create_org_internal(
    db: AsyncSession,
    user: User,
    name: str,
    slug: str,
    is_personal: bool,
    *,
    commit: bool = True,
) -> Organization:
    """Internal helper to create org + owner member."""
    org = await organization_repo.create(
        db,
        name=name,
        slug=slug,
        is_personal=is_personal,
    )

    await organization_repo.create_member(
        db,
        organization_id=org.id,
        user_id=user.id,
        role="owner",
    )

    if commit:
        await db.commit()
        await db.refresh(org)
    else:
        await db.flush()

    return org


async def get_organization_by_id(
    db: AsyncSession,
    org_id: UUID,
) -> Organization | None:
    """Get an organization by ID (excludes deleted)."""
    return await organization_repo.get_by_id(db, organization_id=org_id)


async def update_organization(
    db: AsyncSession,
    org: Organization,
    patch: OrganizationPatchInput,
) -> Organization:
    """Update an organization with partial data."""
    # If slug is being changed, check uniqueness
    if "slug" in patch and await organization_repo.slug_exists(
        db,
        slug=patch["slug"],
        exclude_organization_id=org.id,
    ):
        raise ResourceConflictError("Organization with this slug already exists")

    for field, value in patch.items():
        setattr(org, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ResourceConflictError("Organization with this slug already exists")
    await db.refresh(org)
    return org


async def soft_delete_organization(
    db: AsyncSession,
    org: Organization,
) -> None:
    """Soft delete an organization."""
    if org.is_personal:
        raise InvalidOperationError("Cannot delete personal organization")
    org.is_deleted = True
    org.deleted_at = datetime.now(UTC)
    await db.commit()
