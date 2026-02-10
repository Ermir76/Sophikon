import pytest
from app.core.config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_database_connection():
    """Verify we can connect to the database and run a simple query."""
    # Debug: Print the URL being used
    db_url = settings.DATABASE_URL
    print(f"DEBUG: Testing connection to {db_url}")

    # Ensure it's not empty
    assert db_url, "DATABASE_URL is not set"

    # Create engine locally for this test
    engine = create_async_engine(db_url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            assert val == 1
    finally:
        await engine.dispose()
