from dataclasses import asdict
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.service.auth_service import get_user_by_email
from app.service.organization_service import list_organizations
from scripts.seeding.builders import seed_industry_portfolio
from scripts.seeding.scenario_definitions import get_scenario_pack
from scripts.seeding.upsert import SEED_GENERATOR


@pytest.mark.asyncio
async def test_scenario_pack_is_deterministic_for_fixed_base_date():
    base = date(2026, 3, 1)
    first = get_scenario_pack("mixed-industry", base_date=base)
    second = get_scenario_pack("mixed-industry", base_date=base)

    assert [asdict(item) for item in first] == [asdict(item) for item in second]


@pytest.mark.asyncio
async def test_seed_industry_portfolio_dry_run_does_not_write(
    client: AsyncClient,
    session: AsyncSession,
):
    email = "seed_dryrun@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Seed Dryrun User",
        },
    )

    user = await get_user_by_email(session, email)
    assert user is not None
    orgs, _ = await list_organizations(session, user)
    assert len(orgs) == 1  # exactly 1 personal org after registration
    target_org = orgs[0]
    seed_key = "dry-run-check"

    result = await seed_industry_portfolio(
        session,
        user_email=email,
        org_id=target_org.id,
        seed_key=seed_key,
        base_date=date(2026, 3, 1),
        dry_run=True,
    )

    assert result.dry_run is True
    assert len(result.scenario_runs) == 5

    projects_result = await session.execute(
        select(Project).where(
            Project.organization_id == target_org.id,
            Project.is_deleted == False,  # noqa: E712
        )
    )
    projects = list(projects_result.scalars().all())
    seeded = [
        p
        for p in projects
        if (p.settings or {}).get("seed_meta", {}).get("generator") == SEED_GENERATOR
        and (p.settings or {}).get("seed_meta", {}).get("seed_key") == seed_key
    ]
    assert len(seeded) == 0


@pytest.mark.asyncio
@pytest.mark.filterwarnings(
    "ignore:Identity map already had an identity for.*:sqlalchemy.exc.SAWarning"
)
async def test_seed_industry_portfolio_is_idempotent(
    client: AsyncClient,
    session: AsyncSession,
):
    email = "seed_idempotent@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Seed Idempotent User",
        },
    )

    user = await get_user_by_email(session, email)
    assert user is not None
    orgs, _ = await list_organizations(session, user)
    assert len(orgs) == 1  # exactly 1 personal org after registration
    target_org = orgs[0]
    target_org_id = target_org.id
    seed_key = "idempotent-check"

    first = await seed_industry_portfolio(
        session,
        user_email=email,
        org_id=target_org_id,
        seed_key=seed_key,
        base_date=date(2026, 3, 1),
        dry_run=False,
    )
    second = await seed_industry_portfolio(
        session,
        user_email=email,
        org_id=target_org_id,
        seed_key=seed_key,
        base_date=date(2026, 3, 1),
        dry_run=False,
    )

    assert first.totals["projects_created"] == 5
    assert second.totals["projects_created"] == 0
    assert second.totals["projects_updated"] == 5
    assert first.totals["scenario_errors"] == 0

    projects_result = await session.execute(
        select(Project).where(
            Project.organization_id == target_org_id,
            Project.is_deleted == False,  # noqa: E712
        )
    )
    projects = list(projects_result.scalars().all())
    seeded = [
        p
        for p in projects
        if (p.settings or {}).get("seed_meta", {}).get("generator") == SEED_GENERATOR
        and (p.settings or {}).get("seed_meta", {}).get("seed_key") == seed_key
    ]
    assert len(seeded) == 5
