import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User


@pytest.fixture
async def setup_roles(session: AsyncSession):
    """Seed default project roles."""
    for r_name in ["manager", "member", "viewer"]:
        res = await session.execute(select(Role).where(Role.name == r_name))
        if not res.scalar_one_or_none():
            role = Role(name=r_name, scope="project")
            session.add(role)
    await session.commit()


async def add_project_member(session: AsyncSession, project_id, user_email, role_name):
    """Helper: Add user to project with role."""
    res_u = await session.execute(select(User).where(User.email == user_email))
    user = res_u.scalar_one_or_none()
    assert user

    res_r = await session.execute(select(Role).where(Role.name == role_name))
    role = res_r.scalar_one_or_none()
    assert role

    member = ProjectMember(project_id=project_id, user_id=user.id, role_id=role.id)
    session.add(member)
    await session.commit()
