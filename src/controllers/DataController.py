from .BaseController import BaseController
from fastapi import UploadFile
from typing import Dict, Union
import os

class DataController(BaseController):
    def __init__(self):
        super().__init__()

    async def validate_file(self, file: UploadFile) -> Dict[str, Union[str, bool]]:
        """
        Validates the uploaded file for allowed content type and size limit.

        Returns:
            dict: {
                "valid": bool,
                "reason": str  # None if valid
            }
        """
        allowed_types = self.app_settings.FILE_ALLOWED_TYPES
        max_size = self.app_settings.FILE_MAX_SIZE * 1024 * 1024  # MB to bytes

        if file.content_type not in allowed_types:
            return {
                "valid": False,
                "reason": f"Unsupported file type: {file.content_type}"
            }

        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)

        if size > max_size:
            return {
                "valid": False,
                "reason": f"File size {size / (1024*1024):.2f}MB exceeds limit of {self.app_settings.FILE_MAX_SIZE}MB"
            }

        return {"valid": True, "reason": None}
