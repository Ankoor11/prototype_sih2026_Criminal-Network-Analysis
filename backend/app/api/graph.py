"""
NetraLink AI: Knowledge Graph Operations Router
"""

from typing import Optional
from fastapi import APIRouter, Query
from backend.app.services.graph_service import GraphService

router = APIRouter(prefix="/api/investigations/{investigation_id}/graph", tags=["Graph"])


@router.get("")
def get_graph(
    investigation_id: str,
    entity_id: str = Query("P00561", description="Center entity ID"),
    hops: int = Query(2, ge=1, le=3),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    service = GraphService.get_instance()
    return service.get_subgraph(center_node=entity_id, hops=hops, start_time=start_time, end_time=end_time)


@router.get("/expand")
def expand_graph(
    investigation_id: str,
    entity_id: str = Query(..., description="Target node to expand"),
    hops: int = Query(1, ge=1, le=3)
):
    service = GraphService.get_instance()
    return service.expand_network(entity_id=entity_id, hops=hops)


@router.get("/hidden-paths")
def find_hidden_paths(
    investigation_id: str,
    source_id: str = Query("P00561", description="Source suspect entity ID"),
    target_id: str = Query("P00151", description="Target suspect or asset entity ID")
):
    service = GraphService.get_instance()
    paths = service.find_hidden_paths(source_id=source_id, target_id=target_id)
    return {
        "source": source_id,
        "target": target_id,
        "paths_count": len(paths),
        "paths": paths
    }
