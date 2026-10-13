from loguru import logger
import sys

# Clear default handlers and redirect everything to stderr
logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")

# Optional file logging
logger.add("logs/tuitorin.log", rotation="1 MB", retention="7 days", level="INFO")

def get_logger(name: str):
    return logger.bind(name=name)
