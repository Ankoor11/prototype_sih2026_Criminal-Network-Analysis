"""
NetraLink AI: Pipeline Processing Router
"""

from fastapi import APIRouter
from backend.app.services.ai_pipeline import AIPipelineService

router = APIRouter(prefix="/api/investigations/{investigation_id}/pipeline", tags=["Pipeline"])


@router.post("/run")
def run_pipeline(investigation_id: str):
    result = AIPipelineService.execute_pipeline(investigation_id)
    return result


@router.get("/status")
def get_pipeline_status(investigation_id: str):
    # Returns default completed state or initial template
    stages = [
        {"stage_id": s["id"], "name": s["name"], "description": s["desc"], "status": "COMPLETED", "duration_ms": 25}
        for s in AIPipelineService.STAGES
    ]
    return {
        "investigation_id": investigation_id,
        "pipeline_state": "READY",
        "stages": stages
    }
