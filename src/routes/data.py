from fastapi import FastAPI, APIRouter,Depends,UploadFile
from helper.config import get_settings,Settings
from controllers import DataController


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
    return is_valid
