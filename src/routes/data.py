from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from helper.config import get_settings, Settings
from controllers import DataController, ProjectController
from models import ResponseStatus
import aiofiles


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

    # Validate the uploaded file
    validation_result = await data_controller.validate_file(file)
    if not validation_result['valid']:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Status": validation_result['Status'],
                "reason": validation_result['reason']
            }
        )

    # Generate safe and unique filename path
    safe_path = await data_controller.generate_unique_filename(file.filename, project_id)

    # Save the file chunk by chunk
    async with aiofiles.open(safe_path, 'wb') as out_file:
        while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
            await out_file.write(chunk)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "Status": ResponseStatus.FILE_UPLOAD_SUCCESS.value,
            "file_path": str(safe_path)
        }
    )
