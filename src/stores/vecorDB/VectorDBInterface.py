from abc import ABC, abstractmethod
from typing import List

class VectorDBInterface(ABC):

    @abstractmethod
    def connect(self):
        """Initialize connection to the vector DB."""
        pass

    @abstractmethod
    def disconnect(self):
        """Cleanly close connection."""
        pass

    @abstractmethod
    def is_collection_existed(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        pass

    @abstractmethod
    def list_all_collections(self) -> List[str]:
        """List all available collections."""
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> dict:
        """Return metadata about a collection."""
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """Permanently delete a collection."""
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, 
                          embedding_size: int,
                          do_reset: bool = False):
        """Create a collection with the given embedding size."""
        pass

    @abstractmethod
    def insert_one(self, collection_name: str, text: str, vector: list,
                   metadata: dict = None, record_id: str = None):
        """Insert a single record into the collection."""
        pass

    @abstractmethod
    def insert_many(self, collection_name: str, texts: list, 
                    vectors: list, metadata: list = None, 
                    record_ids: list = None, batch_size: int = 50):
        """Insert multiple records in batch."""
        pass

    @abstractmethod
    def search_by_vector(self, collection_name: str, vector: list, limit: int) -> List:
        """Search by embedding vector."""
        pass
