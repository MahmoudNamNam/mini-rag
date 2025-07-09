from fastapi import FastAPI
from routes import base, data
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.append("./src")


app = FastAPI()

app.include_router(base.base_router)
app.include_router(data.data_router)