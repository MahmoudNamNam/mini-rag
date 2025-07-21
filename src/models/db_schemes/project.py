from pydantic import BaseModel, Field, validator
from typing import Optional
from bson import ObjectId
import re

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

class Project(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    project_id: str = Field(..., min_length=1, description="Name of the project")

    @validator('project_id')
    def validate_project_id(cls, value):
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError("Project ID must be alphanumeric (allowing _ and -).")
        return value

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "project_id": "my_project_123"
            }
        }
