from fastapi import FastAPI, APIRouter,Depends
from helper.config import get_settings,Settings

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
    responses={404: {"description": "Not found"}},
)

@base_router.get("/")
async def health(app_settings: Settings = Depends(get_settings)):
    app_settings = get_settings()
    app_name =app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    app_description = app_settings.APP_DESCRIPTION
    return {
        "app_name": app_name,
        "app_version": app_version,
        "app_description": app_description,
        "status": "running"
    }
