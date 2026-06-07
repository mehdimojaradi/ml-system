from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.core.logging import logger
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
)  # desciption="Database connection pool for async operations"

async_session = async_sessionmaker(
    engine,
    # description="Prevent automatic expiration of objects after commit to allow continued access to their attributes"
    expire_on_commit=False,
    # description="Use AsyncSession for asynchronous database interactions"
    class_=AsyncSession,
)  # description="Async session maker for database interactions"


# description="Dependency function to provide an asynchronous database session for use in API endpoints"
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session  # description="Yield the database session for use in API endpoints, ensuring proper cleanup after use"
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()  # Rollback the transaction on error
            raise
        finally:
            await session.close()


async def init_db() -> None:  # description="Initialize the database by creating all tables defined in the SQLAlchemy models"
    pass
