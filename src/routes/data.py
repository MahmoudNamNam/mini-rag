from fastapi import FastAPI, APIRouter,Depends,UploadFile,status
from fastapi.responses import JSONResponse
from helper.config import get_settings,Settings
from controllers import DataController, ProjectController
from models import ResponseStatus
import os
import aiofiles


data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1","data"],
    responses={404: {"description": "Not found"}},
)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, 
                      file: UploadFile, 
                      app_settings: Settings = Depends(get_settings)):
    """
    Upload data file to the server.
    """
    is_valid = await  DataController().validate_file(file= file)
    if not is_valid['valid']:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Status": is_valid['Status'],
                "reason": is_valid['reason']
            }
        )
    project_dir_path = await ProjectController().get_project_path(project_id=project_id)
    file_path = os.path.join(project_dir_path, file.filename)
    async with aiofiles.open(file_path, 'wb') as out_file:
        while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
            await out_file.write(chunk)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "Status": ResponseStatus.FILE_UPLOAD_SUCCESS.value,
            "file_path": file_path
        }
    )
