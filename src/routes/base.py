from fastapi import FastAPI, APIRouter
import os

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
    responses={404: {"description": "Not found"}},
)

@base_router.get("/")
async def health():
    app_name = os.getenv("APP_NAME", "Mini RAG API")
    app_version = os.getenv("APP_VERSION", "0.1.0")
    app_description = os.getenv("APP_DESCRIPTION", "A minimal RAG application")
    return {
        "app_name": app_name,
        "app_version": app_version,
        "app_description": app_description,
        "status": "running"
    }
