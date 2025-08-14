import logging
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from .db_schemes import DataChunk
from .BaseDataModel import BaseDataModel
from typing import List, Optional

logger = logging.getLogger(__name__)

class ChunkModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client=db_client)

    @classmethod
    async def create_instance(cls, db_client):
        return cls(db_client=db_client)

    async def create_chunk(self, chunk: DataChunk) -> DataChunk:
        logger.info("Attempting to create chunk with order: %d", chunk.chunk_order)
        async with self.db_client() as session:
            try:
                async with session.begin():
                    session.add(chunk)
                    await session.flush()
                    await session.refresh(chunk)
                    logger.info("Chunk created successfully with ID: %s", chunk.chunk_id)
                    return chunk
            except SQLAlchemyError as e:
                logger.exception("Failed to create chunk: %s", str(e))
                raise

    async def get_chunk(self, chunk_id: int) -> Optional[DataChunk]:
        logger.info("Looking for chunk with ID: %s", chunk_id)
        async with self.db_client() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        select(DataChunk).where(DataChunk.chunk_id == chunk_id)
                    )
                    chunk = result.scalar_one_or_none()
                    if not chunk:
                        logger.warning("Chunk with ID %s not found.", chunk_id)
                    return chunk
            except SQLAlchemyError as e:
                logger.exception("Failed to fetch chunk: %s", str(e))
                raise

    async def insert_many_chunks(self, chunks: List[DataChunk], batch_size: int = 100) -> int:
        logger.info("Attempting to insert multiple chunks")
        count = 0
        try:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                async with self.db_client() as session:
                    async with session.begin():
                        session.add_all(batch)
                        count += len(batch)
                        logger.info("Inserted %d chunks in this batch", len(batch))
            logger.info("Successfully inserted %d chunks", count)
            return count
        except SQLAlchemyError as e:
            logger.exception("Failed to insert chunks: %s", str(e))
            raise

    async def delete_chunk_by_project_id(self, project_id: int) -> int:
        logger.info("Deleting chunks for project ID: %s", project_id)
        async with self.db_client() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                    )
                    deleted_count = result.rowcount or 0
                    logger.info("Deleted %d chunks for project ID: %s", deleted_count, project_id)
                    return deleted_count
            except SQLAlchemyError as e:
                logger.exception("Failed to delete chunks: %s", str(e))
                raise

    async def get_project_chunks(self, project_id: int, page_no: int = 1, page_size: int = 50) -> List[DataChunk]:
        logger.info("Retrieving chunks for project ID: %s", project_id)
        if page_no < 1: page_no = 1
        if page_size < 1 or page_size > 100: page_size = 50
        offset = (page_no - 1) * page_size

        async with self.db_client() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        select(DataChunk)
                        .where(DataChunk.chunk_project_id == project_id)
                        .order_by(DataChunk.chunk_order)
                        .offset(offset)
                        .limit(page_size)
                    )
                    chunks = result.scalars().all()
                    logger.info("Retrieved %d chunks for project ID: %s", len(chunks), project_id)
                    return chunks
            except SQLAlchemyError as e:
                logger.exception("Failed to retrieve chunks: %s", str(e))
                raise
