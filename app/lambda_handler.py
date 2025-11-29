from mangum import Mangum
from app.main import app

# Create the Lambda handler
# Mangum wraps the FastAPI app to make it compatible with AWS Lambda
handler = Mangum(app, lifespan="off")
