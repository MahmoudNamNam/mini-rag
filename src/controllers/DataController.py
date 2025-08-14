import logging
import os
import re
from typing import Dict, Union, Tuple
from fastapi import UploadFile
from .BaseController import BaseController
from .ProjectController import ProjectController
from models import ResponseStatus

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(name)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class DataController(BaseController):
    def __init__(self):
        super().__init__()
        logger.info("DataController initialized.")

    async def validate_file(self, file: UploadFile) -> Dict[str, Union[str, bool, None]]:
        logger.info(f"Validating file: {file.filename} with content type {file.content_type}")
        allowed_types = self.app_settings.FILE_ALLOWED_TYPES
        max_size = self.app_settings.FILE_MAX_SIZE * 1024 * 1024  # Convert MB to bytes

        if file.content_type not in allowed_types:
            logger.warning(f"Unsupported file type: {file.content_type}")
            return {
                "valid": False,
                "Status": ResponseStatus.FILE_TYPE_NOT_SUPPORTED.value,
                "reason": f"Unsupported file type: {file.content_type}"
            }

        try:
            file.file.seek(0, os.SEEK_END)
            size = file.file.tell()
            file.file.seek(0)
            logger.info(f"File size: {size} bytes")
        except Exception as e:
            logger.error(f"Error checking file size: {e}")
            return {
                "valid": False,
                "Status": ResponseStatus.FILE_VALIDATION_FAILED.value,
                "reason": f"Error during file size check: {str(e)}"
            }

        if size > max_size:
            logger.warning(f"File size exceeded: {size} bytes (Limit: {max_size} bytes)")
            return {
                "valid": False,
                "Status": ResponseStatus.FILE_SIZE_EXCEEDED.value,
                "reason": f"File size {size / (1024*1024):.2f}MB exceeds limit of {self.app_settings.FILE_MAX_SIZE}MB"
            }

        logger.info("File validation passed.")
        return {
            "valid": True,
            "Status": ResponseStatus.FILE_UPLOAD_SUCCESS.value,
        }

    async def generate_unique_filepath(self, orig_file_name: str, project_id: int) -> Tuple[str, str]:
        logger.info(f"Generating unique filepath for file: {orig_file_name}, project ID: {project_id}")
        random_key = self.generate_unique_key(length=12)
        project_path = ProjectController().get_project_path(project_id=project_id)
        cleaned_name = self.get_cleaned_filename(orig_file_name)[:100]
        unique_filename = f"{random_key}_{cleaned_name}"
        new_file_path = os.path.join(project_path, unique_filename)

        while os.path.exists(new_file_path):
            logger.debug(f"File exists: {new_file_path}. Generating new key.")
            random_key = self.generate_unique_key(length=12)
            unique_filename = f"{random_key}_{cleaned_name}"
            new_file_path = os.path.join(project_path, unique_filename)

        logger.info(f"Generated unique file path: {new_file_path}")
        return new_file_path, unique_filename

    def get_cleaned_filename(self, orig_file_name: str) -> str:
        logger.debug(f"Cleaning filename: {orig_file_name}")
        cleaned = re.sub(r'[^a-zA-Z0-9_.-]', '_', orig_file_name.strip())
        logger.debug(f"Cleaned filename: {cleaned}")
        return cleaned
