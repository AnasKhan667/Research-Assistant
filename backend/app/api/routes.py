import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app.agent import ResearchOrchestrator
from app.config import config
from app.models.schemas import FindingResponse, HealthResponse, ResearchRequest, ResearchResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# The orchestrator loads an LLM endpoint - build it once and reuse across requests.
_orchestrator: ResearchOrchestrator | None = None


def get_orchestrator() -> ResearchOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ResearchOrchestrator()
    return _orchestrator


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok")


@router.post("/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    orchestrator = get_orchestrator()

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(orchestrator.generate_report, request.query.strip()),
            timeout=config.REQUEST_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error("Research timed out after %ds for query=%r", config.REQUEST_TIMEOUT, request.query[:80])
        raise HTTPException(
            status_code=504,
            detail=f"Research timed out after {config.REQUEST_TIMEOUT}s. Try a more specific query.",
        )
    except Exception as e:
        logger.exception("Research process failed for query=%r", request.query[:80])
        raise HTTPException(status_code=500, detail=f"Research process failed: {e}")

    return ResearchResponse(
        query=result["query"],
        plan=result.get("plan"),
        final_report=result.get("final_report"),
        iteration_count=result.get("iteration_count", 0),
        findings=[
            FindingResponse(content=f.content, source=f.source)
            for f in result.get("research_findings", [])
        ],
        sources=result.get("sources", []),
    )
