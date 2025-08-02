from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from helper.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from routes import base, data, nlp  # Keep all routes

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
        vectordb_provider_factory = VectorDBProviderFactory(config=settings)
        app.vectordb_client = vectordb_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)

        if not app.vectordb_client:
            raise ValueError(f"Invalid VECTOR_DB_BACKEND: {settings.VECTOR_DB_BACKEND}")

        app.vectordb_client.connect()
        logger.info("VectorDB client initialized successfully")
    except Exception:
        logger.exception("Failed to initialize VectorDB provider")
        raise

    yield

    # Shutdown logic
    app.mongodb_client.close()
    logger.info("MongoDB client closed")

    app.vectordb_client.disconnect()
    logger.info("VectorDB client disconnected")


# FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Register routes
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
