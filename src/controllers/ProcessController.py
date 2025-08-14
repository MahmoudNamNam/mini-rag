import os
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Optional: Add handler if none exists (to avoid duplicate logs if already configured globally)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

from .BaseController import BaseController
from .ProjectController import ProjectController
from langchain_community.document_loaders import (
    TextLoader, PyMuPDFLoader, Docx2txtLoader
)
from models import ProcessingEnums
from langchain_text_splitters import RecursiveCharacterTextSplitter

class ProcessController(BaseController):
    def __init__(self, project_id: int):
        """
        Initializes the ProcessController with a specific project.
        """
        super().__init__()
        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)
        self.loader_registry = {
            ProcessingEnums.TXT.value: TextLoader,
            ProcessingEnums.PDF.value: PyMuPDFLoader,
            ProcessingEnums.DOCX.value: Docx2txtLoader,
        }

    def get_file_extension(self, file_id: str) -> str:
        """
        Extracts and normalizes the file extension from a file ID or name.
        """
        return os.path.splitext(file_id)[-1].lower()

    def get_file_loader(self, file_id: str):
        """
        Returns the appropriate LangChain document loader for the given file.
        Raises FileNotFoundError or ValueError as appropriate.
        """
        file_extension = self.get_file_extension(file_id)
        file_path = os.path.join(self.project_path, file_id)

        if not os.path.exists(file_path):
            logger.error(f"File not found at path: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        loader_cls = self.loader_registry.get(file_extension)
        if not loader_cls:
            supported = ", ".join(self.loader_registry.keys())
            logger.error(f"Unsupported file type '{file_extension}'. Supported types: {supported}")
            raise ValueError(
                f"Unsupported file type '{file_extension}'. "
                f"Supported types are: {supported}"
            )

        logger.info(f"Using loader {loader_cls.__name__} for file: {file_path}")
        return loader_cls(file_path)

    def get_file_content(self, file_id: str):
        """
        Loads and returns the content of the specified file using the appropriate loader.
        """
        try:
            loader = self.get_file_loader(file_id=file_id)
            documents = loader.load()
            logger.info(f"Successfully loaded {len(documents)} documents from {file_id}")
            return documents
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Error loading file {file_id}: {e}")
            raise

    def process_file_content(self, file_content: list, file_id: str, chunk_size: int = 1000, overlap_size: int = 200):
        """
        Processes the content of the specified file and returns the text split into chunks.

        Args:
            file_content (list): List of Document-like objects with `page_content` and `metadata` attributes.
            file_id (str): Identifier for logging/debugging purposes.
            chunk_size (int): Max characters per chunk.
            overlap_size (int): Overlap between consecutive chunks.

        Returns:
            list: List of chunked Document objects.
        """
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap_size,
                length_function=len
            )

            valid_docs = [(doc.page_content, doc.metadata) for doc in file_content 
                          if hasattr(doc, 'page_content') and hasattr(doc, 'metadata')]

            if not valid_docs:
                logger.warning(f"No valid documents found in file {file_id}. Returning empty list.")
                return []

            file_content_text, file_content_metadata = zip(*valid_docs) if valid_docs else ([], [])

            if not file_content_text:
                logger.warning(f"No text content found in file {file_id}. Returning empty list.")
                return []

            chunks = text_splitter.create_documents(file_content_text, metadatas=file_content_metadata)
            logger.info(f"Created {len(chunks)} chunks from {file_id} with chunk size {chunk_size} and overlap {overlap_size}")
            return chunks

        except Exception as e:
            logger.error(f"Error processing file {file_id}: {e}")
            raise
