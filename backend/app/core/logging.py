import os
from loguru import logger
from .config import settings

logger.remove()  # Remove default logger

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')

LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{function}:{line} - "
    "{message}"
)

logger.add(
    sink=os.path.join(LOG_DIR, "debug.log"),
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="10 MB",  # Rotate log files when they reach 10 MB
    retention="30 days",  # Keep log files for 30 days
    compression="zip"  # Compress rotated log files
)

logger.add(
    sink=os.path.join(LOG_DIR, "error.log"),
    format=LOG_FORMAT,
    level="ERROR",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    backtrace=True,  # Include stack trace for error logs
    diagnose=True  # Include variable values in stack trace
)