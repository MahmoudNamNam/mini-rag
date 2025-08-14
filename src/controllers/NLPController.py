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

    def create_collection_name(self, project_id: int):
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
    
    def search_vector_db_collection(self, project: Project, query: str, limit: int = 10):
        collection_name = self.create_collection_name(project_id=project.project_id)
        logger.info(f"Searching in collection: {collection_name} with query: {query}")

        try:
            query_vector = self.embedding_client.embed_text(
                text=query,
                document_type=DocumentTypeEnum.QUERY.value
            )
            if not query_vector:
                logger.error("Failed to embed query text.")
                raise ValueError("Embedding returned an empty vector.")

            results = self.vectordb_client.search_by_vector(
                collection_name=collection_name,
                vector=query_vector,
                limit=limit
            )

            if not results:
                logger.warning(f"No results found for query: {query}")
                return []

            logger.info(f"Search completed with {len(results)} results.")
            return results

        except Exception as e:
            logger.exception(f"Error occurred during vector DB search: {e}")
            raise

    def answer_rag_question(self, project: Project, question: str, limit: int = 5):
        logger.info(f"[RAG] Answering question for project: {project.project_id} | Q: {question}")

        search_results = self.search_vector_db_collection(
            project=project,
            query=question,
            limit=limit
        )

        if not search_results:
            logger.warning("[RAG] No search results found for the given question.")
            return {
                "question": question,
                "answer": None,
                "context": "",
                "full_prompt": "",
                "chat_history": [],
                "error": "No relevant documents found."
            }

        context = "\n".join([doc.text for doc in search_results])

        try:
            system_prompt = self.template_parser.get("rag", "system_prompt") or ""
            footer_prompt = self.template_parser.get("rag", "footer_prompt", vars={"query": question}) or ""
        except Exception as e:
            logger.exception("[RAG] Error retrieving system/footer prompt.")
            return {"error": "Template loading failed"}

        documents_prompts = "\n".join([
            self.template_parser.get(
                group="rag",
                key="document_prompt",
                vars={
                    "doc_num": idx + 1,
                    "chunk_text":self.generation_client.process_text(doc.text),
                }
            ) or f"[Doc {idx+1}] {doc.text}"
            for idx, doc in enumerate(search_results)
        ])

        full_prompt = "\n\n".join([documents_prompts, footer_prompt])

        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value
            )
        ]

        try:
            answer = self.generation_client.generate_text(
                prompt=full_prompt,
                chat_history=chat_history,
                max_output_tokens=self.generation_client.default_output_max_tokens,
                temperature=self.generation_client.default_generation_temperature
            )
            logger.info("[RAG] Answer successfully generated.")
        except Exception as e:
            logger.exception("[RAG] Generation failed.")
            return {"error": "LLM generation failed"}

        return {
            "question": question,
            "answer": answer,
            "context": context,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        }



            

