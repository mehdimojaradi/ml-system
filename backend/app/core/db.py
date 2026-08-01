import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import text
from sqlalchemy.pool import AsyncAdaptedQueuePool

from backend.app.core.logging import logger
from backend.app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    # this line configures the connection pool to use AsyncAdaptedQueuePool,
    # which is suitable for async database interactions and provides efficient connection management for high-concurrency applications.
    poolclass=AsyncAdaptedQueuePool,
    # description="Enable pre-ping to check the health of connections before using them"
    pool_pre_ping=True,
    pool_size=5,  # description="Maximum number of connections in the pool"
    # description="Maximum number of connections that can be created beyond the pool size"
    max_overflow=10,
    pool_timeout=30,  # description="Maximum time to wait for a connection from the pool before raising an error"
    # description="Recycle connections after this many seconds to prevent stale connections"
    pool_recycle=1800,
)  # desciption="Database connection pool for async operations"

async_session = async_sessionmaker(
    engine,
    # description="Prevent automatic expiration of objects after commit to allow continued access to their attributes"
    expire_on_commit=False,
    # description="Use AsyncSession for asynchronous database interactions"
    class_=AsyncSession,
)  # description="Async session maker for database interactions"


# description="Dependency function to provide an asynchronous database session for use in API endpoints"
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = async_session()
    try:
        yield session  # description="Yield the session for use in API endpoints, allowing for proper cleanup after use"
    except Exception as e:
        # description="Log any exceptions that occur during session usage"
        logger.error(f"Database session error: {e}")
        if session:
            try:
                await session.rollback()  # description="Rollback the transaction on error"
                # description="Log that the session was rolled back"
                logger.info("Database session rolled back due to error")
            except Exception as rollback_error:
                # description="Log any exceptions that occur during rollback"
                logger.error(f"Error during rollback: {rollback_error}")
        raise  # description="Re-raise the original exception after handling"
    finally:
        if session:
            try:
                await session.close()  # description="Ensure the session is closed after use"
                # description="Log that the session was closed successfully"
                logger.info("Database session closed successfully")
            except Exception as close_error:
                # description="Log any exceptions that occur during session close"
                logger.error(f"Error closing database session: {close_error}")


async def init_db() -> None:  # description="Initialize the database by creating all tables defined in the SQLAlchemy models"
    try:
        max_retries = 3  # description="Maximum number of retries for database initialization"
        retry_delay = 2  # description="Delay in seconds between retries"
        
        for attempt in range(max_retries):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))  # description="Test the database connection"
                logger.info("Database connection successful") 
                break  # description="Exit the retry loop if the connection is successful"
            except Exception as e:
                logger.error(f"Failed to verfity database connection after {max_retries} attempts: {e}")
                raise  # description="Re-raise the exception if all retries fail"
            logger.warning(f"Database connection failed on attempt {attempt + 1}")
            await asyncio.sleep(retry_delay * (attempt + 1))  # description="Wait before retrying the connection"
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise  # description="Re-raise the exception to be handled by the caller"