#!/usr/bin/env python3
import logging
import uvicorn
from fastapi import FastAPI
from endpoints import router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S',
)

logger = logging.getLogger(__name__)

# Swagger/OpenAPI metadata
app = FastAPI(
    title="Archie Backend API",
    description="""
    Backend API for Archie - a conversational AI system.
    
    ## Features
    
    * **Conversations**: Create and manage conversations
    * **Messages**: Send and retrieve messages within conversations
    
    ## Endpoints
    
    * `/conversations` - Manage conversations
    * `/messages` - Manage messages within conversations
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc documentation
    openapi_url="/openapi.json"
)
app.include_router(router)

logger.info("=== STEP 1: App Init ===")
logger.info(f"main_001: FastAPI ready")

if __name__ == "__main__":
    logger.info(f"main_002: Starting server on \033[36m0.0.0.0:8000\033[0m")
    uvicorn.run(app, host="0.0.0.0", port=8000)
