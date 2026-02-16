import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    """Register creates a user, returns user data, and sets auth cookies."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    # User data is nested under "user"
    user = data["user"]
    assert user["email"] == "newuser@example.com"
    assert user["full_name"] == "New User"
    assert "id" in user
    assert user["is_active"] is True

    # Tokens structure exists (values are empty because they're in cookies)
    assert "tokens" in data

    # Auth cookies are set
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
