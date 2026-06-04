from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.logging import logger
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
) #desciption="Database connection pool for async operations"

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False, #description="Prevent automatic expiration of objects after commit to allow continued access to their attributes"
    class_=AsyncSession, #description="Use AsyncSession for asynchronous database interactions"
)#description="Async session maker for database interactions"

async def get_db() -> AsyncGenerator[AsyncSession, None]: #description="Dependency function to provide an asynchronous database session for use in API endpoints"
    async with async_session() as session:
        try:
            yield session #description="Yield the database session for use in API endpoints, ensuring proper cleanup after use"
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()  # Rollback the transaction on error
            raise   
        finally:            
            await session.close()
            
async def init_db() -> None: #description="Initialize the database by creating all tables defined in the SQLAlchemy models"
    pass