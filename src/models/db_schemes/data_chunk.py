<<<<<<< HEAD
from pydantic import BaseModel, Field
from typing import Optional, Dict
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class DataChunk(BaseModel):
    """
    Represents a chunk of data with metadata.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    file_name: str = Field(..., description="Name of the file from which this chunk was created")
    chunk_index: int = Field(..., ge=0, description="Index of the chunk in the file")
    chunk_content: str = Field(..., min_length=1, description="Content of the data chunk")
    chunk_metadata: Optional[Dict] = Field(default=None, description="Additional metadata for the chunk")
    chunk_project_id: Optional[PyObjectId] = Field(default=None, description="Project ID for chunking purposes")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "project_id": "my_project_123",
                "file_name": "example.txt",
                "chunk_index": 0,
                "content": "This is a sample data chunk.",
                "metadata": {"source": "user_upload"}
            }
        }
=======
from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class DataChunk(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., gt=0)
    chunk_project_id: ObjectId

    class Config:
        arbitrary_types_allowed = True
>>>>>>> b9f47690f59584ba4f7ced78d7dd3fdb93248047
