from fastapi import FastAPI, APIRouter,Depends,UploadFile,status
from fastapi.responses import JSONResponse
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
    if not is_valid['valid']:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Status": is_valid['Status'],
                "reason": is_valid['reason']
            }
        )
    return is_valid
