
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status,Request
from fastapi.responses import JSONResponse
from helper.config import get_settings, Settings
from .schema import ProcessRequest
from controllers import DataController,ProcessController
from models import ResponseStatus
import aiofiles
import logging
from models.ProjectModel import ProjectModel

logger = logging.getLogger(__name__)

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
    responses={404: {"description": "Not found"}},
)

@data_router.post("/upload/{project_id}")
async def upload_data(
    request: Request,
    project_id: str,
    file: UploadFile,
    app_settings: Settings = Depends(get_settings)
):
    """
    Upload a data file to the server for a specific project.
    """
    project_model = ProjectModel(db_client= request.app.mongodb_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

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

@data_router.post("/process/{project_id}")
async def process_endpoint(project_id: str, process_request: ProcessRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    process_controller = ProcessController(project_id=project_id)
    file_content = process_controller.get_file_content(file_id=file_id)

    if not file_content:
        logger.warning(f"No content found for file '{file_id}' in project '{project_id}'")
        raise HTTPException(
            ResponseStatus.PROCESSING_FAILED.value,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No content found for file '{file_id}' in project '{project_id}'"
        )

    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )

    logger.info(f"Processed {len(file_chunks)} chunks for file '{file_id}' in project '{project_id}'")

    chunks_serialized = [
        {"content": doc.page_content, "metadata": doc.metadata}
        for doc in file_chunks
    ]

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "Status": ResponseStatus.PROCESSING_SUCCESS.value,
            "file_id": file_id,
            "chunks": chunks_serialized
        }
    )
