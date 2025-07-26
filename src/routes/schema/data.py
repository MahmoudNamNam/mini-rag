from pydantic import BaseModel, Field
from typing import Optional

class ProcessRequest(BaseModel):
    """
    Request model for processing data.
    """
    file_id: Optional[str] = Field(default=None, description="Unique identifier for the file to be processed")
    chunk_size: Optional[int] = Field(default=1024 * 1024, description="Size of each chunk in bytes, default is 1MB")
    overlap_size: Optional[int] = Field(default=20, description="Size of overlap between chunks in bytes, default is 20")
    do_reset: Optional[int] = Field(default=0, description="Data processing reset flag, default is 0 (no reset)")
