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


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Register — duplicate email returns 409"""
    email = "duplicate@example.com"
    password = "StrongPassword123!"

    # First registration
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "First User",
        },
    )

    # Second registration with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "AnotherPassword456!",
            "full_name": "Second User",
        },
    )

    assert response.status_code == 409
    assert "already registered" in response.text


@pytest.mark.asyncio
async def test_register_missing_fields(client: AsyncClient):
    """Register — missing required fields returns 422"""
    # Missing email
    resp1 = await client.post(
        "/api/v1/auth/register",
        json={
            "password": "StrongPassword123!",
            "full_name": "No Email",
        },
    )
    assert resp1.status_code == 422

    # Missing password
    resp2 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nopassword@example.com",
            "full_name": "No Password",
        },
    )
    assert resp2.status_code == 422

    # Missing name
    resp3 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "noname@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert resp3.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Register — weak password (less than 8 chars) returns 422"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weakpass@example.com",
            "password": "short",  # < 8 chars
            "full_name": "Weak Password",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Register — invalid email format returns 422"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123!",
            "full_name": "Invalid Email",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Success — valid credentials return user data + set cookies (200)"""
    email = "login_success@example.com"
    password = "StrongPassword123!"

    # 1. Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Login User",
        },
    )

    # 2. Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == email
    # Check cookies are set
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Login — wrong password returns 401"""
    email = "wrong_password@example.com"
    password = "StrongPassword123!"

    # 1. Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Login User",
        },
    )

    # 2. Login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "WrongPassword!",
        },
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.asyncio
async def test_login_non_existent_email(client: AsyncClient):
    """Login — non-existent email returns 401"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "doesntexist@example.com",
            "password": "SomePassword123!",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_missing_fields(client: AsyncClient):
    """Login — missing required fields returns 422"""
    # Missing email
    resp1 = await client.post(
        "/api/v1/auth/login",
        json={
            "password": "StrongPassword123!",
        },
    )
    assert resp1.status_code == 422

    # Missing password
    resp2 = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
        },
    )
    assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient):
    """Success — valid refresh cookie rotates tokens (200)"""
    email = "refresh@example.com"
    password = "StrongPassword123!"

    # 1. Register to get tokens
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Refresh User",
        },
    )
    assert register_response.status_code == 201

    # client automatically stores cookies from register_response

    # 2. Refresh
    # Need to wait a tiny bit? Probably not for functional test unless
    # there is a strict "not before" check that fails instantly.
    # Usually refresh is allowed immediately.

    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 200

    # Check new tokens
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    # Verify we can user new access token
    # (By calling /me or similar, but test plan doesn't strictly require it here,
    # just checking 200 and cookies is enough for "rotates tokens")


@pytest.mark.asyncio
async def test_refresh_token_missing_cookie(client: AsyncClient):
    """Refresh — missing cookie returns 401"""
    # Simply call refresh without logging in first.
    # The client fixture is fresh for each test.
    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert "No refresh token found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient):
    """Success — revokes token, clears cookies (200)"""
    email = "logout@example.com"
    password = "StrongPassword123!"

    # 1. Register and get cookies
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Logout User",
        },
    )

    # 2. Call logout
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"

    # 3. Check cookies are cleared (usually by setting them to empty or expired)
    # Be careful: AsyncClient might just remove them or set them to ""
    # We should check if they are NOT present or empty.

    # Actually, httpx client updates cookies based on Set-Cookie headers.
    # If server sends Set-Cookie: access_token="", then client.cookies['access_token'] might be ""

    # Let's check if we can access protected route.
    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_logout_idempotent(client: AsyncClient):
    """Idempotent — no error when called without cookies (200)"""
    # Calling logout without being logged in should succeed (idempotent)
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


@pytest.mark.asyncio
async def test_get_current_user_success(client: AsyncClient):
    """Authenticated — returns current user (200)"""
    email = "me@example.com"
    password = "StrongPassword123!"

    # 1. Register and get cookies
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Me User",
        },
    )

    # 2. Get current user
    # Cookie is sent automatically by client
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()

    # Assert fields are present
    assert data["email"] == email
    assert data["full_name"] == "Me User"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_current_user_unauthenticated(client: AsyncClient):
    """Unauthenticated — returns 401"""
    # Simply call without logging in.
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]
