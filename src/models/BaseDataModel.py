import logging
from typing import List
from helper.config import get_settings, Settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(name)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class BaseDataModel:
    """
    Base data model class for handling common functionality across data models.
    """
    def __init__(self, db_client: object):
        self.db_client = db_client
        self.settings = get_settings()
        logger.info("BaseDataModel initialized with DB name: %s", self.settings.MONGO_DB_NAME)
    
    def get_collection(self, collection_name: str):
        logger.debug("Accessing collection: %s", collection_name)
        return self.db_client[self.settings.MONGO_DB_NAME][collection_name]

    async def init_collection_with_indexes(self, collection_name: str, indexes: List[dict]):
        logger.info("Initializing collection '%s' with indexes...", collection_name)
        db = self.db_client[self.settings.MONGO_DB_NAME]
        existing_collections = await db.list_collection_names()

        if collection_name not in existing_collections:
            logger.info("Creating new collection: %s", collection_name)
            col = self.get_collection(collection_name)

            for idx in indexes:
                try:
                    await col.create_index(idx["key"], name=idx["name"], unique=idx.get("unique", False))
                    logger.info("Created index '%s' on '%s'", idx["name"], idx["key"])
                except Exception as e:
                    logger.error("Error creating index '%s': %s", idx.get("name", str(idx)), str(e))
        else:
            logger.info("Collection '%s' already exists. Skipping index creation.", collection_name)
