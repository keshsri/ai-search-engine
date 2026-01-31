"""
Lambda handler for AWS Lambda integration with FastAPI.
Uses Mangum to adapt ASGI application to Lambda event format.
"""

from mangum import Mangum
from app.main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")
