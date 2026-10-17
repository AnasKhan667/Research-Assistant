from typing import List, Optional

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class FindingResponse(BaseModel):
    content: str
    source: Optional[str] = None


class ResearchResponse(BaseModel):
    query: str
    plan: Optional[str] = None
    final_report: Optional[str] = None
    iteration_count: int
    findings: List[FindingResponse]
    sources: List[str]


class HealthResponse(BaseModel):
    status: str
