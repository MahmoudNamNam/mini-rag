from enum import Enum

class ResponseStatus(Enum):
    """
    Enum representing response status codes for file upload and validation operations.
    """

    FILE_VALIDATION_SUCCESS = "file_validation_success"
    FILE_VALIDATED_SUCCESS = "file_validate_successfully"
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
    PROJECT_NOT_FOUND = "project_not_found"
    NO_ASSETS_FOUND = "no_assets_found"
    NO_FILES_ERROR = "not_found_files"
    FILE_ID_ERROR = "no_file_found_with_this_id"
