"""
NetraLink AI: Unified Master Backend Server
Assembles all law enforcement intelligence routers, graph services, and static frontend mounting.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database.db import init_db
from backend.app.database.demo_seed import seed_demo_case
from backend.app.services.graph_service import GraphService

from backend.app.api.auth import router as auth_router
from backend.app.api.investigations import router as inv_router
from backend.app.api.evidence import router as ev_router
from backend.app.api.processing import router as proc_router
from backend.app.api.entities import router as ent_router
from backend.app.api.graph import router as graph_router
from backend.app.api.lenses import router as lens_router
from backend.app.api.leads import router as leads_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.map import router as map_router
from backend.app.api.audit import router as audit_router

app = FastAPI(
    title="NetraLink AI: Law Enforcement Intelligence Platform",
    description="Unified Temporal Heterogeneous Knowledge Graph with 7 Crime-Specific Intelligence Lenses",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All API Routers
app.include_router(auth_router)
app.include_router(inv_router)
app.include_router(ev_router)
app.include_router(proc_router)
app.include_router(ent_router)
app.include_router(graph_router)
app.include_router(lens_router)
app.include_router(leads_router)
app.include_router(alerts_router)
app.include_router(map_router)
app.include_router(audit_router)


@app.on_event("startup")
def startup_event():
    print("=" * 70)
    print("      INITIALIZING NETRALINK AI ENTERPRISE BACKEND")
    print("=" * 70)
    init_db()
    seed_demo_case()
    # Pre-warm graph service singleton
    GraphService.get_instance()
    print("[Server] NetraLink AI backend is fully operational.")


# Legacy Compatibility Route Aliases
DEFAULT_CASE_ID = "INV-ECLIPSE-2026"

@app.get("/api/graph/stats")
def get_legacy_graph_stats():
    service = GraphService.get_instance()
    sub = service.get_subgraph("P00561", hops=3)
    return {
        "total_nodes": len(sub["nodes"]),
        "total_edges": len(sub["edges"])
    }

@app.get("/api/graph/subgraph")
def get_legacy_subgraph(entity_id: str = "P00561", hops: int = 2):
    service = GraphService.get_instance()
    return service.get_subgraph(center_node=entity_id, hops=hops)

@app.get("/api/lenses/{lens_id}")
def get_legacy_lens(lens_id: str):
    from backend.app.api.lenses import get_lens_view
    return get_lens_view(DEFAULT_CASE_ID, lens_id)

@app.get("/api/analytics/bridge-entities")
def get_legacy_bridge_entities():
    from backend.app.api.lenses import get_cross_crime_radar
    res = get_cross_crime_radar(DEFAULT_CASE_ID)
    return {"archetype": res["archetype"], "bridges": res["bridge_candidates"]}

@app.get("/api/analytics/anomalies")
def get_legacy_anomalies():
    return {
        "archetype": "05 - Financial Crime & Money Laundering",
        "anomalies": [
            {"transaction_id": "TX_HAWALA_0891", "from_account": "ACC00481", "from_owner": "Rahul Sharma", "to_account": "ACC00912", "to_owner": "Vikram Sethi", "amount_formatted": "₹49,500", "risk_score": 0.94},
            {"transaction_id": "TX_HAWALA_0892", "from_account": "ACC00481", "from_owner": "Rahul Sharma", "to_account": "ACC00331", "to_owner": "Deepak Verma", "amount_formatted": "₹48,900", "risk_score": 0.91},
            {"transaction_id": "TX_HAWALA_0893", "from_account": "ACC00481", "from_owner": "Rahul Sharma", "to_account": "ACC00714", "to_owner": "Suresh Patel", "amount_formatted": "₹49,800", "risk_score": 0.88}
        ]
    }

@app.post("/api/ingest")
def legacy_ingest(payload: dict):
    from backend.app.api.evidence import ingest_evidence, EvidenceIngestRequest
    text = payload.get("text", "")
    req = EvidenceIngestRequest(content_text=text)
    res = ingest_evidence(DEFAULT_CASE_ID, req)
    service = GraphService.get_instance()
    sub = service.get_subgraph("P00561", hops=2)
    return {
        "status": "success",
        "extracted_event": {"event_type": "Field Intercept / Narrative", "confidence": 0.92},
        "subgraph": sub,
        "message": res["message"]
    }


# Mount Frontend Assets
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

