from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helper.config import get_settings, Settings
from controllers import DataController
from models import ResponseStatus
import aiofiles
import logging

logger = logging.getLogger(__name__)  # Use module-level logger

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
    responses={404: {"description": "Not found"}},
)

@data_router.post("/upload/{project_id}")
async def upload_data(
    project_id: str,
    file: UploadFile,
    app_settings: Settings = Depends(get_settings)
):
    """
    Upload a data file to the server for a specific project.
    """
    data_controller = DataController()
    logger.info(f"Received upload request for project: {project_id}, file: {file.filename}")

    # Step 1: Validate the file
    validation_result = await data_controller.validate_file(file)
    if not validation_result['valid']:
        logger.warning(f"Validation failed for file '{file.filename}': {validation_result['reason']}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Status": validation_result['Status'],
                "reason": validation_result['reason']
            }
        )

    # Step 2: Generate a unique, safe file path
    try:
        safe_path,file_id = await data_controller.generate_unique_filepath(file.filename, project_id)
    except Exception as e:
        logger.error(f"Failed to generate file path for project '{project_id}': {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Status": ResponseStatus.FILE_UPLOAD_FAILED.value,
                "reason": "File path generation failed"
            }
        )

    # Step 3: Save the file in chunks
    try:
        async with aiofiles.open(safe_path, 'wb') as out_file:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await out_file.write(chunk)
        logger.info(f"File '{file.filename}' uploaded successfully to '{safe_path}' for project '{project_id}'")
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Status": ResponseStatus.FILE_UPLOAD_FAILED.value,
                "reason": str(e)
            }
        )

    # Step 4: Return success response with metadata
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "Status": ResponseStatus.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id,
            "file_path": str(safe_path),
        }
    )
