from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from helper.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from routes import base, data
from stores.vecorDB.VectorDBProviderFactory import VectorDBProviderFactory



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # MongoDB connection
    try:
        app.mongodb_client = AsyncIOMotorClient(settings.MONGO_URI)
        app.mongodb = app.mongodb_client[settings.MONGO_DB_NAME]
        await app.mongodb.command("ping")
        logger.info("Connected to MongoDB")
    except Exception:
        logger.exception("Failed to connect to MongoDB")
        raise

    # LLM Initialization
    try:
        llm_provider_factory = LLMProviderFactory(config=settings)

        app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
        if not app.generation_client:
            raise ValueError(f"Invalid GENERATION_BACKEND: {settings.GENERATION_BACKEND}")
        app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

        app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
        if not app.embedding_client:
            raise ValueError(f"Invalid EMBEDDING_BACKEND: {settings.EMBEDDING_BACKEND}")
        app.embedding_client.set_embedding_model(
            model_id=settings.EMBEDDING_MODEL_ID,
            embedding_size=settings.EMBEDDING_MODEL_SIZE
        )

        logger.info("LLM clients initialized successfully")
    except Exception:
        logger.exception("Failed to initialize LLM providers")
        raise

    # VectorDB Initialization
    try:
        vector_db_factory = VectorDBProviderFactory(config=settings)
        app.vector_db_client = vector_db_factory.create(provider=settings.VECTOR_DB_BACKEND)

        if not app.vector_db_client:
            raise ValueError(f"Invalid VECTOR_DB_BACKEND: {settings.VECTOR_DB_BACKEND}")
        await app.vector_db_client.connect()
        logger.info("VectorDB client initialized successfully")
    except Exception:
        logger.exception("Failed to initialize VectorDB provider")
        raise

    # Yield control to app
    yield

    # Shutdown logic
    app.mongodb_client.close()
    logger.info("MongoDB client closed")

    app.vector_db_client.disconnect()
    logger.info("VectorDB client disconnected")


# FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Register routes
app.include_router(base.base_router)
app.include_router(data.data_router)
