import logging
from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId
from pymongo import InsertOne
from typing import List

# Configure logger for this module
logger = logging.getLogger(__name__)

class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.DATABASE_NAME.value][DataBaseEnum.COLLECTION_CHUNK_NAME.value]
    
        logger.info("ChunkModel initialized with collection: %s", self.collection.name)

    async def create_chunk(self, chunk: DataChunk):
        logger.info("Attempting to create chunk with order: %d", chunk.chunk_order)
        try:
            result = await self.collection.insert_one(chunk.dict(by_alias=True, exclude_unset=True))
            chunk.id = result.inserted_id
            logger.info("Chunk created successfully with ObjectId: %s", result.inserted_id)
            return chunk
        except Exception as e:
            logger.exception("Failed to create chunk with order %d: %s", chunk.chunk_order, str(e))
            raise
    
    async def get_chunk(self, chunk_id: str):
        logger.info("Looking for chunk with ID: %s", chunk_id)
        try:
            record = await self.collection.find_one({"_id":ObjectId(chunk_id)})
            if record is None:  
                logger.warning("Chunk with ID %s not found.", chunk_id)
                return None
            
            logger.info("Found chunk with ID: %s", chunk_id)
            return DataChunk(**record)
        except Exception as e:
            logger.exception("Failed to fetch chunk with ID %s: %s", chunk_id, str(e))
            raise

    async def insert_many_chunks(self, chunks: List[DataChunk],batch_size: int = 100):
        logger.info("Attempting to insert multiple chunks")
        try:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                operations = [InsertOne(chunk.dict(by_alias=True, exclude_unset=True)) for chunk in batch]
                result = await self.collection.bulk_write(operations)
                logger.info("Inserted %d chunks in this batch", len(batch))
            logger.info("Successfully inserted %d chunks", len(chunks))
            return len(chunks)
        except Exception as e:
            logger.exception("Failed to insert chunks: %s", str(e))
            raise