
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status,Request
from fastapi.responses import JSONResponse
from helper.config import get_settings, Settings
from .schema import ProcessRequest
from controllers import DataController,ProcessController
from models import ResponseStatus
import aiofiles
import logging
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemes import DataChunk,Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
from bson import ObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

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
    project_model = await ProjectModel.create_instance(db_client= request.app.mongodb_client)
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
    # Step 4: Create an Asset record
    asset_model = await AssetModel.create_instance(db_client=request.app.mongodb_client)
    asset_resource = Asset(
        asset_project_id=ObjectId(project.id),
        asset_type=AssetTypeEnum.DOCUMENT,
        asset_name=file_id,
        asset_size=os.path.getsize(safe_path),
    )
    try:
        asset = await asset_model.create_asset(asset=asset_resource)
        logger.info(f"Asset created successfully with ID: {asset.id}")
    except Exception as e:
        logger.error(f"Failed to create asset record: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Status": ResponseStatus.FILE_UPLOAD_FAILED.value,
                "reason": "Asset creation failed"
            }
        )
    

    # Step 5: Return success response with metadata
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "Status": ResponseStatus.FILE_UPLOAD_SUCCESS.value,
            "file_id": str(asset.id),
            "file_path": str(safe_path),

        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id: str, process_request: ProcessRequest):
    logger.info(f"Starting file processing for project_id: {project_id}")

    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    logger.debug(f"chunk_size: {chunk_size}, overlap_size: {overlap_size}, do_reset: {do_reset}")

    try:
        project_model = await ProjectModel.create_instance(
            db_client=request.app.mongodb_client
        )
        project = await project_model.get_project_or_create_one(
            project_id=project_id
        )
        logger.info(f"Project resolved: {project_id} -> {project.id}")
    except Exception as e:
        logger.exception(f"Failed to initialize or retrieve project: {project_id}")
        raise

    asset_model = await AssetModel.create_instance(
        db_client=request.app.mongodb_client
    )

    project_files_ids = {}

    try:
        if process_request.file_id:
            logger.info(f"Fetching specific file: {process_request.file_id}")
            asset_record = await asset_model.get_asset_record(
                asset_project_id=project.id,
                asset_name=process_request.file_id
            )

            if asset_record is None:
                logger.warning(f"No file found with name: {process_request.file_id}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": ResponseStatus.FILE_ID_ERROR.value}
                )

            project_files_ids = {asset_record.id: asset_record.asset_name}
        else:
            logger.info(f"Fetching all DOCUMENT-type assets for project: {project.id}")
            project_files = await asset_model.get_all_project_assets(
                asset_project_id=project.id,
                asset_type=AssetTypeEnum.DOCUMENT.value,
            )
            project_files_ids = {
                record.id: record.asset_name for record in project_files
            }

        if len(project_files_ids) == 0:
            logger.warning(f"No documents found for project: {project.id}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": ResponseStatus.NO_FILES_ERROR.value}
            )
    except Exception as e:
        logger.exception(f"Failed to retrieve project files for project: {project_id}")
        raise

    process_controller = ProcessController(project_id=project_id)

    no_records = 0
    no_files = 0

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.mongodb_client
    )

    if do_reset == 1:
        logger.info(f"Reset flag is set. Deleting old chunks for project: {project.id}")
        deleted_count = await chunk_model.delete_chunks_by_project_id(project_id=project.id)
        logger.info(f"Deleted {deleted_count} old chunks")

    for asset_id, file_id in project_files_ids.items():
        try:
            logger.info(f"Processing file: {file_id}")
            file_content = process_controller.get_file_content(file_id=file_id)

            if file_content is None:
                logger.error(f"No content returned for file: {file_id}")
                continue

            file_chunks = process_controller.process_file_content(
                file_content=file_content,
                file_id=file_id,
                chunk_size=chunk_size,
                overlap_size=overlap_size
            )

            if not file_chunks:
                logger.warning(f"No chunks generated for file: {file_id}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"status": ResponseStatus.PROCESSING_FAILED.value}
                )

            file_chunks_records = [
                DataChunk(
                    chunk_text=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                    chunk_order=i + 1,
                    chunk_project_id=project.id,
                    chunk_asset_id=asset_id
                )
                for i, chunk in enumerate(file_chunks)
            ]

            inserted = await chunk_model.insert_many_chunks(chunks=file_chunks_records)
            no_records += inserted
            no_files += 1

            logger.info(f"File {file_id} processed: {inserted} chunks inserted.")
        except Exception as e:
            logger.exception(f"Error occurred while processing file {file_id}")

    logger.info(f"Processing completed. Total files: {no_files}, Total chunks: {no_records}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "Status": ResponseStatus.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files
        }
    )