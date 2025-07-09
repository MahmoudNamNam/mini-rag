from enum import Enum

class ResponseStatus(Enum):
    """
    Enum representing response status codes for file upload and validation operations.
    """

    FILE_VALIDATION_SUCCESS = "file_validation_success"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    PROCESSING_SUCCESS = "processing_success"
    PROCESSING_FAILED = "processing_failed"
    FILE_NOT_FOUND = "file_not_found"
    FILE_ALREADY_EXISTS = "file_already_exists"
    FILE_DELETION_SUCCESS = "file_deletion_success"
    FILE_DELETION_FAILED = "file_deletion_failed"
