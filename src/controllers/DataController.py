from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from typing import Dict, Union
import os
from models import ResponseStatus
import re


class DataController(BaseController):
    def __init__(self):
        super().__init__()

    async def validate_file(self, file: UploadFile) -> Dict[str, Union[str, bool, None]]:
        """
        Validates the uploaded file for allowed content type and size limit.
        """
        allowed_types = self.app_settings.FILE_ALLOWED_TYPES
        max_size = self.app_settings.FILE_MAX_SIZE * 1024 * 1024  # MB to bytes

        if file.content_type not in allowed_types:
            return {
                "valid": False,
                "Status": ResponseStatus.FILE_TYPE_NOT_SUPPORTED.value,
                "reason": f"Unsupported file type: {file.content_type}"
            }

        try:
            file.file.seek(0, os.SEEK_END)
            size = file.file.tell()
            file.file.seek(0)
        except Exception as e:
            return {
                "valid": False,
                "Status": ResponseStatus.FILE_VALIDATION_FAILED.value,
                "reason": f"Error during file size check: {str(e)}"
            }

        if size > max_size:
            return {
                "valid": False,
                "Status": ResponseStatus.FILE_SIZE_EXCEEDED.value,
                "reason": f"File size {size / (1024*1024):.2f}MB exceeds limit of {self.app_settings.FILE_MAX_SIZE}MB"
            }

        return {
            "valid": True,
            "Status": ResponseStatus.FILE_UPLOAD_SUCCESS.value,
            "reason": None
        }

    async def generate_unique_filepath(self, orig_file_name: str, project_id: str) -> str:
        """
        Generates a unique, sanitized filename under the project directory.
        """
        random_key = self.generate_unique_key(length=12)
        project_path = await ProjectController().get_project_path(project_id=project_id)
        cleaned_name = self.get_cleaned_filename(orig_file_name)
        unique_filename = f"{random_key}_{cleaned_name}"
        new_file_path = os.path.join(project_path, unique_filename)

        while os.path.exists(new_file_path):
            random_key = self.generate_unique_key(length=12)
            unique_filename = f"{random_key}_{cleaned_name}"
            new_file_path = os.path.join(project_path, unique_filename)
        
        return new_file_path,unique_filename

    def get_cleaned_filename(self, orig_file_name: str) -> str:
        """
        Cleans the filename by removing special characters and spaces.
        """
        return re.sub(r'[^a-zA-Z0-9_.-]', '_', orig_file_name.strip())
