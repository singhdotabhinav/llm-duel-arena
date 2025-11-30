import logging
import os
from mangum import Mangum
from app.main import app

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logger = logging.getLogger()
logger.setLevel(log_level)

# Ensure root logger has a handler if not present (Lambda usually provides one)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

logger.info(f"Initializing Lambda Handler with Log Level: {log_level}")

# Create the Lambda handler
# Mangum wraps the FastAPI app to make it compatible with AWS Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """
    Wrapper to add extra debug logging before passing to Mangum
    """
    logger.debug(f"Received event: {event}")
    return handler(event, context)

