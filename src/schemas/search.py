from pydantic import BaseModel

class WebSearchRequest(BaseModel):
    query: str

class WebSearchResponse(BaseModel):
    query: str
    answer: str
    sources: str
