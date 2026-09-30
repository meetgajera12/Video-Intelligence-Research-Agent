from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class User(BaseModel):
    yt_url: HttpUrl = Field(..., description='URL of youtube video.')
    question: Optional[str] = Field(default=None, description='Questions related to uploaded youtube video.')