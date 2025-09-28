#!/usr/bin/env python3
import logging
import uvicorn
from fastapi import FastAPI
from endpoints import router

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

logger.info("Archie AI Agent application started")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
