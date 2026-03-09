from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.organization import Organization
from app.models.user import User


@pytest.mark.asyncio
async def test_register_creates_personal_org(client: AsyncClient):
    """
    Integration: Register -> Personal Org auto-created -> Appears in Org List.
    """
    # 1. Register
    email = "new_user_auth_flow@example.com"
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Auth Flow User",
        },
    )
    assert resp.status_code == 201

    # 2. List Organizations
    # The user should be automatically logged in (cookies set)
    org_resp = await client.get("/api/v1/organizations")
    assert org_resp.status_code == 200
    items = org_resp.json()["items"]

    # Verify at least one org exists (Personal Org)
    assert len(items) >= 1
    # Optional: Verify name format if known, but existence is key here.


@pytest.mark.asyncio
async def test_token_rotation_security(client: AsyncClient):
    """
    Integration: Refresh Token Rotation -> Old token invalidated.
    """
    # 1. Register (login)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "token_flow_user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Token Flow User",
        },
    )

    # Capture initial cookies
    # Note: client.cookies automatically manages them.
    # We need to extract the refresh token value to manually send it later.
    refresh_token_1 = client.cookies.get("refresh_token")
    assert refresh_token_1

    # 2. Refresh (Rotates token)
    resp_ref = await client.post("/api/v1/auth/refresh")
    assert resp_ref.status_code == 200
    refresh_token_2 = client.cookies.get("refresh_token")

    # Verify token changed
    assert refresh_token_2 != refresh_token_1

    # 3. Try to use Old Refresh Token
    # We need to clear cookies and manually set the old one.
    client.cookies.clear()
    client.cookies.set("refresh_token", refresh_token_1)

    # Attempt refresh again
    resp_reuse = await client.post("/api/v1/auth/refresh")

    # Should be 401 Unauthorized (Token Reuse Detection or simply Invalid Token)
    assert resp_reuse.status_code == 401


@pytest.mark.asyncio
async def test_register_atomic_failure(client: AsyncClient, session):
    """
    If token creation fails, neither the user nor the org should be committed.
    """
    email = "fail_atomic@example.com"
    with patch(
        "app.service.auth_service._create_token_pair",
        side_effect=Exception("Simulated failure"),
    ):
        with pytest.raises(Exception, match="Simulated failure"):
            await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "StrongPassword123!",
                    "full_name": "Atomic Fail User",
                },
            )

    # User should not exist
    user_resp = await session.execute(select(User).where(User.email == email))
    assert user_resp.scalar_one_or_none() is None

    # Org should not exist
    org_resp = await session.execute(
        select(Organization).where(Organization.slug == "fail-atomic")
    )
    assert org_resp.scalar_one_or_none() is None
