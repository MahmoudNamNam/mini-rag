from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json
import logging

logger = logging.getLogger(__name__)


class NLPController(BaseController):

    def __init__(self, vectordb_client, generation_client, 
                 embedding_client, template_parser):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()

    def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        logger.info(f"Resetting collection: {collection_name}")
        return self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        logger.info(f"Fetching collection info: {collection_name}")
        collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)
        return json.loads(json.dumps(collection_info, default=lambda x: x.__dict__))

    def index_into_vector_db(self, project: Project, chunks: List[DataChunk],
                             chunks_ids: List[int], do_reset: bool = False):
        collection_name = self.create_collection_name(project_id=project.project_id)
        logger.info(f"Indexing {len(chunks)} chunks into vector DB collection: {collection_name} (reset={do_reset})")

        texts = [c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]
        vectors = [
            self.embedding_client.embed_text(text=text, document_type=DocumentTypeEnum.DOCUMENT.value)
            for text in texts
        ]

        self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )

        self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            record_ids=chunks_ids,
        )

        logger.info(f"Successfully indexed into collection: {collection_name}")
        return True

