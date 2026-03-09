import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role


@pytest.fixture
async def setup_roles(session: AsyncSession):
    """Seed default project roles."""
    for r_name in ["owner", "manager", "member", "viewer"]:
        res = await session.execute(select(Role).where(Role.name == r_name))
        if not res.scalar_one_or_none():
            role = Role(name=r_name, scope="project")
            session.add(role)
    await session.commit()
