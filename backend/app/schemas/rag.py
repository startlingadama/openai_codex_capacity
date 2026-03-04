from pydantic import BaseModel, Field


class RagSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    k: int = Field(default=5, ge=1, le=10)


class RagSearchResponse(BaseModel):
    results: list[dict]
