from fastapi import FastAPI
from .api.main import api_router
from .core.config import settings
from contextlib import asynccontextmanager
from .core.db import init_db

@asynccontextmanager #description="Lifespan context manager to handle application startup and shutdown events, including database initialization"
async def lifespan(app: FastAPI): #description="Lifespan function to initialize the database before the application starts and perform any necessary cleanup on shutdown"
    await init_db()  # Initialize the database before the application starts
    yield  # Yield control to the application
    # Perform any necessary cleanup here (if needed)



app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan  # Use the lifespan context manager for startup and shutdown events
)

app.include_router(api_router, prefix=settings.API_V1_STR)
