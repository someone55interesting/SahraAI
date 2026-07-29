from pydantic import BaseModel

class YouTubeSummaryRequest(BaseModel):
    url: str

class YouTubeSummaryResponse(BaseModel):
    video_id: str
    summary: str
