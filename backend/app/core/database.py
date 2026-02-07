from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from collections.abc import AsyncGenerator
from app.core.config import settings

# Create the connection to the database
# - echo: print all database commands (only in development)
# - pool_size: keep 5 connections always ready
# - max_overflow: allow 10 extra connections when busy
# - pool_pre_ping: check if connection is alive before using it

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENV == "development",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# A factory that creates new "conversations" with the database
# - expire_on_commit=False: keep data available after saving
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# The parent class that all our database tables will inherit from
class Base(DeclarativeBase):
    pass


# Give each API request its own conversation with the database
# The conversation closes automatically when the request is done
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
