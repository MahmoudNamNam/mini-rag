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
        self.collection = self.get_collection(DataBaseEnum.COLLECTION_CHUNK_NAME.value)
    
        logger.info("ChunkModel initialized with collection: %s", self.collection.name)

    @classmethod
    async def create_instance(cls, db_client: object):
        """
        Factory method to create an instance of ChunkModel.
        """
        instance = cls(db_client=db_client)
        await instance.init_collection()
        return instance
  
    async def init_collection(self):
        indexes = DataChunk.get_indexes()
        await self.init_collection_with_indexes(
            DataBaseEnum.COLLECTION_CHUNK_NAME.value,
            indexes
        )

    async def create_chunk(self, chunk: DataChunk):
        logger.info("Attempting to create chunk with order: %d", chunk.chunk_order)
        try:
            result = await self.collection.insert_one(chunk.model_dump(by_alias=True, exclude_unset=True))
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
                operations = [InsertOne(chunk.model_dump(by_alias=True, exclude_unset=True)) for chunk in batch]
                result = await self.collection.bulk_write(operations)
                logger.info("Inserted %d chunks in this batch", len(batch))
            logger.info("Successfully inserted %d chunks", len(chunks))
            return len(chunks)
        except Exception as e:
            logger.exception("Failed to insert chunks: %s", str(e))
            raise
    
    async def delete_chunk_by_project_id(self, project_id: ObjectId) -> int:
        """
        Delete all chunks associated with a given project_id.

        Args:
            project_id (ObjectId): The unique identifier of the project.

        Returns:
            int: The number of deleted chunk documents.
        """
        logger.info("Attempting to delete chunks for project ID: %s", str(project_id))
        try:
            result = await self.collection.delete_many({"chunk_project_id": project_id})
            logger.info("Deleted %d chunks for project ID: %s", result.deleted_count, str(project_id))
            return result.deleted_count
        except Exception as e:
            logger.exception("Failed to delete chunks for project ID %s: %s", str(project_id), str(e))
            raise
