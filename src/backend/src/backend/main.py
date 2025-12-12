"""XM Spotify Sync - Main Application Entry Point."""

import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import initialize_sync_service, router, shutdown_sync_service
from backend.config import get_settings

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting XM Spotify Sync service...")
    try:
        await initialize_sync_service()
    except Exception as e:
        logger.error(f"Failed to start sync service: {e}")
    yield
    await shutdown_sync_service()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": "0.1.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


def main():
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
