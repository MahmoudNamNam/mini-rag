from .BaseController import BaseController
from fastapi import UploadFile
from typing import Dict, Union
import os
from models import ResponseStatus

class DataController(BaseController):
    def __init__(self):
        super().__init__()

    async def validate_file(self, file: UploadFile) -> Dict[str, Union[str, bool, None]]:
        """
        Validates the uploaded file for allowed content type and size limit.

        Returns:
            dict: {
                "valid": bool,
                "Status": str,
                "reason": str | None
            }
        """
        allowed_types = self.app_settings.FILE_ALLOWED_TYPES
        max_size = self.app_settings.FILE_MAX_SIZE * 1024 * 1024  # MB to bytes

        if file.content_type not in allowed_types:
            return {
                "valid": False,
                "Status": ResponseStatus.FILE_TYPE_NOT_SUPPORTED.value,
                "reason": f"Unsupported file type: {file.content_type}"
            }

        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)

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
