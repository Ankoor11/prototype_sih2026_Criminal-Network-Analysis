"""
NetraLink AI: Entities & Resolution Workbench Router
"""

from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.graph_service import GraphService

router = APIRouter(prefix="/api/investigations/{investigation_id}/entities", tags=["Entities"])


class ResolutionDecisionRequest(BaseModel):
    candidate_id: str
    decision: str  # CONFIRM, REJECT, FLAG
    notes: str = ""


@router.get("")
def get_entities(investigation_id: str):
    service = GraphService.get_instance()
    return service.get_entities_breakdown()


@router.get("/resolution/candidates")
def get_resolution_candidates(investigation_id: str):
    service = GraphService.get_instance()
    return {"candidates": service.get_resolution_candidates()}


@router.post("/resolution/decide")
def decide_resolution(investigation_id: str, payload: ResolutionDecisionRequest):
    service = GraphService.get_instance()
    res = service.resolve_candidate(payload.candidate_id, payload.decision, payload.notes)
    return res
