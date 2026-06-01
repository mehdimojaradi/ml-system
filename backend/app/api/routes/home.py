from fastapi import APIRouter
from app.core.logging import logger

router = APIRouter(prefix="/home", tags=["home"])

@router.get("/")
def home():    
    logger.info("Home endpoint accessed")
    return {"message": "Welcome to the Home Page!"}