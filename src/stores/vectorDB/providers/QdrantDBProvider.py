from qdrant_client import models, QdrantClient
from qdrant_client.models import PointStruct
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
from typing import List
import time
from models.db_schemes import RetrievedDocument


class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_client: str, default_vector_size: int = 786,
                                     distance_method: str = None, index_threshold: int=100):
        self.logger = logging.getLogger(__name__)
        # self.logger = logging.getLogger('uvicorn')
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.debug("Initializing QdrantDBProvider...")

        self.client = None
        self.db_client = db_client
        self.distance_method = None
        self.default_vector_size = default_vector_size

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT
        
        self.index_threshold = index_threshold
        self.logger.debug(f"QdrantDBProvider initialized with db_client: {db_client}, "
                          f"default_vector_size: {default_vector_size}, "
                          f"distance_method: {self.distance_method}, "
                          f"index_threshold: {index_threshold}")
        
    def connect(self):
        self.logger.debug("Connecting to QdrantDB...")
        try:
            if not self.db_client:
                raise ValueError("No db_client provided for QdrantDB connection.")

            if self.db_client == ":memory:":
                self.client = QdrantClient(location=":memory:")
                self.logger.debug("Connected to in-memory QdrantDB.")
            elif self.db_client.startswith("http://") or self.db_client.startswith("https://"):
                self.client = QdrantClient(url=self.db_client)
                self.logger.debug(f"Connected to remote QdrantDB at {self.db_client}")
            else:
                self.client = QdrantClient(path=self.db_client)
                self.logger.debug(f"Connected to local QdrantDB at {self.db_client}")

        except Exception as e:
            self.logger.error(f"Failed to connect to QdrantDB: {e}")
            raise

    def disconnect(self):
        self.logger.debug("Disconnecting from QdrantDB...")
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                self.logger.warning(f"Error during Qdrant client close: {e}")
            finally:
                self.client = None
                self.logger.debug("Disconnected from QdrantDB.")
        else:
            self.logger.warning("No active QdrantDB client to disconnect.")

    def is_collection_existed(self, collection_name: str) -> bool:
        self.logger.debug(f"Checking if collection '{collection_name}' exists...")

        if not self.client:
            self.logger.error("QdrantDB client is not connected.")
            raise ValueError("QdrantDB client is not connected.")

        try:
            exists = self.client.collection_exists(collection_name=collection_name)
            self.logger.debug(f"Collection '{collection_name}' exists: {exists}")
            return exists
        except Exception as e:
            self.logger.error(f"Error checking collection existence: {e}")
            return False
        
    def list_all_collections(self) -> List:
        self.logger.debug("Listing all collections...")
        
        if not self.client:
            self.logger.error("QdrantDB client is not connected.")
            raise ValueError("QdrantDB client is not connected.")

        try:
            response = self.client.get_collections()
            collection_names = [col.name for col in response.collections]
            self.logger.debug(f"Found collections: {collection_names}")
            return collection_names
        except Exception as e:
            self.logger.error(f"Error retrieving collections: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> dict:
        self.logger.debug(f"Retrieving info for collection '{collection_name}'...")

        if not self.client:
            self.logger.error("QdrantDB client is not connected.")
            raise ValueError("QdrantDB client is not connected.")

        try:
            info = self.client.get_collection(collection_name=collection_name)
            self.logger.debug(f"Retrieved collection info: {info}")
            return info.model_dump() 
        except Exception as e:
            self.logger.error(f"Error retrieving collection info: {e}")
            return {}
    
    def delete_collection(self, collection_name: str):
        self.logger.debug(f"Attempting to delete collection '{collection_name}'...")

        if not self.client:
            self.logger.error("QdrantDB client is not connected.")
            raise ValueError("QdrantDB client is not connected.")

        try:
            if self.is_collection_existed(collection_name):
                self.logger.info(f"Deleting collection: {collection_name}")
                result = self.client.delete_collection(collection_name=collection_name)
                self.logger.debug(f"Collection '{collection_name}' deletion result: {result}")
                return result
            else:
                self.logger.warning(f"Collection '{collection_name}' does not exist. Nothing to delete.")
                return None
        except Exception as e:
            self.logger.error(f"Error while deleting collection '{collection_name}': {e}")
            return None

    def create_collection(
        self, 
        collection_name: str, 
        embedding_size: int, 
        do_reset: bool = False
    ) -> bool:
        self.logger.debug(f"Preparing to create collection '{collection_name}' "
                        f"(reset={do_reset}, embedding_size={embedding_size})")

        if not self.client:
            self.logger.error("QdrantDB client is not connected.")
            raise ValueError("QdrantDB client is not connected.")

        try:
            if do_reset:
                self.delete_collection(collection_name=collection_name)

            if not self.is_collection_existed(collection_name):
                self.logger.info(f"Creating new Qdrant collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=embedding_size,
                        distance=self.distance_method
                    )
                )
                self.logger.debug(f"Collection '{collection_name}' created successfully.")
                return True
            else:
                self.logger.info(f"Collection '{collection_name}' already exists. Skipping creation.")
                return False
        except Exception as e:
            self.logger.error(f"Error creating collection '{collection_name}': {e}")
            return False
        


    def insert_one(self, collection_name: str, text: str, vector: list,
                        metadata: dict = None, 
                        record_id: str = None) -> bool:
        
        self.logger.debug(f"Starting insert_one into collection '{collection_name}'")

        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Cannot insert record: collection '{collection_name}' does not exist.")
            return False

        record = models.Record(
            id=record_id,
            vector=vector,
            payload={
                "text": text,
                "metadata": metadata
            }
        )

        self.logger.debug(f"Prepared record for insertion: id={record_id}, vector_dim={len(vector)}, text_len={len(text)}, metadata_keys={list(metadata.keys()) if metadata else []}")

        start_time = time.time()

        try:
            self.client.upload_records(
                collection_name=collection_name,
                records=[record]
            )
            duration = time.time() - start_time
            self.logger.info(f"Record inserted successfully into '{collection_name}' (id={record_id}) in {duration:.3f} sec")
            return True

        except Exception as e:
            self.logger.error(f"Error inserting record into '{collection_name}' (id={record_id}): {e}")
            return False


    def insert_many(self, collection_name: str, texts: list, 
                        vectors: list, metadata: list = None, 
                        record_ids: list = None, batch_size: int = 50) -> bool:
        
        self.logger.debug(f"Starting insert_many into '{collection_name}' with {len(texts)} records")

        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Cannot insert records: collection '{collection_name}' does not exist.")
            return False

        if not (len(texts) == len(vectors)):
            self.logger.error("Length mismatch: 'texts' and 'vectors' must have same length.")
            return False

        if metadata is None:
            metadata = [None] * len(texts)
        if record_ids is None:
            record_ids = [str(i) for i in range(len(texts))]

        if not (len(metadata) == len(texts) == len(record_ids)):
            self.logger.error("Length mismatch: All inputs must have the same length.")
            return False

        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.Record(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x],
                        "metadata": batch_metadata[x]
                    }
                )
                for x in range(len(batch_texts))
            ]

            try:
                start_time = time.time()
                self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records,
                )
                duration = time.time() - start_time
                self.logger.info(f"Inserted batch {i // batch_size + 1} ({len(batch_records)} records) into '{collection_name}' in {duration:.2f}s")

            except Exception as e:
                self.logger.error(f"Error inserting batch {i // batch_size + 1} into '{collection_name}': {e}")
                return False

        self.logger.info(f"Successfully inserted all {len(texts)} records into '{collection_name}'")
        return True


    def search_by_vector(self, collection_name: str, vector: list, limit: int = 5)-> List[RetrievedDocument]:
        self.logger.debug(f"Searching in '{collection_name}' with vector of dim={len(vector)} and limit={limit}")

        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Search failed: Collection '{collection_name}' does not exist.")
            return None

        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit
            )

            if not results or len(results) == 0:
                self.logger.info(f"No results found for vector search in '{collection_name}'")
                return None



            self.logger.info(f"Search returned {len(results)} results from '{collection_name}'")
            return [
                RetrievedDocument(
                    text=result.payload.get("text", ""),
                    score=result.score
                ) for result in results
            ]

        except Exception as e:
            self.logger.error(f"Error during vector search in '{collection_name}': {e}")
            return None
