from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    AsyncTransaction,
    create_async_engine,
)

from app.core.config import settings
from app.core.database import get_db
from app.main import app

# ---------------------------------------------------------------------------
# Database fixtures — savepoint-based rollback
#
# How it works:
#   1. connection fixture: opens a real DB connection, shared per test
#   2. transaction fixture: begins a transaction on that connection
#   3. client fixture: creates sessions with join_transaction_mode="create_savepoint"
#      so when service code calls `await db.commit()`, it only commits a savepoint
#      inside the outer transaction — not a real commit
#   4. After the test, the outer transaction is rolled back — everything disappears
# ---------------------------------------------------------------------------


@pytest.fixture()
async def connection() -> AsyncGenerator[AsyncConnection]:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.connect() as conn:
        yield conn
    await engine.dispose()


@pytest.fixture()
async def transaction(connection: AsyncConnection) -> AsyncGenerator[AsyncTransaction]:
    async with connection.begin() as txn:
        yield txn


@pytest.fixture(autouse=True)
def disable_rate_limiter():
    """Disable rate limiting for all tests."""
    app.state.limiter.enabled = False


@pytest.fixture(autouse=True)
def _mock_mail_globally(monkeypatch):
    """
    Prevent ALL tests from sending real emails.

    Without this, any test that registers a user will trigger
    send_verification_email → real Gmail SMTP → bounce-back spam.
    """

    mock_client = MagicMock()
    mock_client.send_message = AsyncMock()
    monkeypatch.setattr(
        "app.service.email_service._get_mail_client",
        lambda: mock_client,
    )


@pytest.fixture()
async def client(
    connection: AsyncConnection,
    transaction: AsyncTransaction,
) -> AsyncGenerator[AsyncClient]:
    """
    Test client that uses a savepoint-wrapped session.

    Any db.commit() inside service code only commits a savepoint.
    After the test, the outer transaction is rolled back.
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        async with session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()
    await transaction.rollback()


@pytest.fixture()
async def session(
    connection: AsyncConnection,
) -> AsyncGenerator[AsyncSession]:
    """
    Direct DB session for tests that need to insert data outside the API.

    Shares the same connection (and transaction) as the client fixture,
    so rows inserted here are visible to API endpoints during the test.
    """
    session = AsyncSession(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    async with session:
        yield session
