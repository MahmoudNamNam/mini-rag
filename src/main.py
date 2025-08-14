from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from helper.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectorDB.VectorDBProviderFactory import VectorDBProviderFactory
from routes import base, data, nlp
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
try:
    import colorlog

    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - [%(levelname)s] - %(name)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red',
        }
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  
    root_logger.handlers = [handler]

except ImportError:
    logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # PostgreSQL connection
    try:
        postgres_conn = (
            f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:"
            f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
            f"{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
        )
        app.db_engine = create_async_engine(postgres_conn, echo=False)
        app.db_client = sessionmaker(
            bind=app.db_engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("Connected to PostgreSQL")
    except Exception:
        logger.exception("Failed to connect to PostgreSQL")
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

    # Template Parser Initialization
    try:
        app.template_parser = TemplateParser(
            language=settings.PRIMARY_LANG,
            default_language=settings.DEFAULT_LANG
        )
        logger.info("Template parser initialized successfully")
    except Exception:
        logger.exception("Failed to initialize Template Parser")
        raise

    yield

    # Shutdown logic
    try:
        await app.db_engine.dispose()
        logger.info("PostgreSQL engine disposed")
    except Exception:
        logger.exception("Failed to dispose PostgreSQL engine")

    try:
        app.vectordb_client.disconnect()
        logger.info("VectorDB client disconnected")
    except Exception:
        logger.exception("Failed to disconnect VectorDB client")

# FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Register routes
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
