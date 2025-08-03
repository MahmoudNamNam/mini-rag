from pydantic import BaseModel, Field
from typing import Optional

class PushRequest(BaseModel):
    do_reset: Optional[int] = Field(
        default=0,
        description="Whether to reset the vector DB collection before indexing. 1 = reset, 0 = append."
    )

class SearchRequest(BaseModel):
    query_text: str
    limit: Optional[int] = 10