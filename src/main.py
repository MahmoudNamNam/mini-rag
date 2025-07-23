from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from routes import base, data

from helper.config import get_settings
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    try:
        app.mongodb_client = AsyncIOMotorClient(settings.MONGO_URI)
        app.mongodb = app.mongodb_client[settings.MONGO_DB_NAME]
        await app.mongodb.command("ping")
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.exception("Error connecting to MongoDB")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    app.mongodb_client.close()
    logger.info("MongoDB client closed")

app.include_router(base.base_router)
app.include_router(data.data_router)
