"""
NetraLink AI: FastAPI Backend Server
Provides REST APIs for Graph Exploration, 7 Crime Intelligence Lenses,
Syndicate Bridge Detection, Financial Anomaly Scoring, and Real-Time Text Ingestion.
"""

import os
import sys
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from netralink.graph.temporal_kg import TemporalKnowledgeGraph
from netralink.nlp.event_extractor import EventExtractor
from netralink.analytics.syndicate_bridge_detector import SyndicateBridgeDetector
from netralink.analytics.financial_anomaly import FinancialAnomalyDetector

app = FastAPI(
    title="NetraLink AI Intelligence Engine",
    description="Unified Temporal Heterogeneous Knowledge Graph with 7 Crime-Specific Intelligence Lenses",
    version="1.0.0"
)

# Global in-memory singletons
tkg: Optional[TemporalKnowledgeGraph] = None
extractor: Optional[EventExtractor] = None
bridge_detector: Optional[SyndicateBridgeDetector] = None
anomaly_detector: Optional[FinancialAnomalyDetector] = None

# Cached analytics
cached_bridges: List[Dict[str, Any]] = []
cached_anomalies: List[Dict[str, Any]] = []


def initialize_engine():
    """Initializes the graph and pre-calculates core analytics."""
    global tkg, extractor, bridge_detector, anomaly_detector, cached_bridges, cached_anomalies

    if tkg is not None:
        return

    print("[Engine] Initializing NetraLink Knowledge Graph...")
    tkg = TemporalKnowledgeGraph()
    tkg.load_nodes("dataset/raw")
    tkg.load_communications("dataset/raw")
    tkg.load_transactions("dataset/raw")
    tkg.load_geo_events("dataset/raw")
    tkg.load_extracted_nlp_edges("data/processed/extracted_graph_edges.csv")

    extractor = EventExtractor()
    bridge_detector = SyndicateBridgeDetector(tkg)
    anomaly_detector = FinancialAnomalyDetector(tkg, data_dir="dataset")

    print("[Engine] Pre-calculating Syndicate Bridge entities & Financial anomalies...")
    cached_bridges = bridge_detector.run_detection(top_k=20)
    cached_anomalies = anomaly_detector.detect_anomalies(top_k=25)
    print(f"[Engine] Ready with {tkg.graph.number_of_nodes()} nodes and {tkg.graph.number_of_edges()} edges.")


@app.on_event("startup")
def on_startup():
    initialize_engine()


# -----------------------------------------------------------------------------
# REST API ENDPOINTS
# -----------------------------------------------------------------------------
@app.get("/api/health")
def get_health():
    return {
        "status": "online",
        "engine": "NetraLink AI 1.0",
        "nodes": tkg.graph.number_of_nodes() if tkg else 0,
        "edges": tkg.graph.number_of_edges() if tkg else 0
    }


@app.get("/api/graph/stats")
def get_graph_stats():
    """Returns total node and edge breakdowns."""
    if not tkg:
        raise HTTPException(status_code=503, detail="Engine initializing")
    return tkg.get_statistics()


@app.get("/api/graph/subgraph")
def get_subgraph(
    entity_id: str = Query("P00561", description="Center entity ID (e.g. P00561, P00072, PH01018)"),
    hops: int = Query(2, ge=1, le=3, description="Neighborhood depth"),
    start_time: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_time: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Returns an egocentric neighborhood graph around an entity in Cytoscape.js format.
    """
    if not tkg:
        raise HTTPException(status_code=503, detail="Engine initializing")

    sub = tkg.get_subgraph(entity_id, hops=hops, start_time=start_time, end_time=end_time)
    if sub.number_of_nodes() == 0:
        # Fallback: if node not found, return top bridge suspect subgraph
        if cached_bridges:
            fallback_id = cached_bridges[0]["entity_id"]
            sub = tkg.get_subgraph(fallback_id, hops=hops, start_time=start_time, end_time=end_time)

    return tkg.to_cytoscape_json(sub)


@app.get("/api/analytics/bridge-entities")
def get_bridge_entities(top_k: int = Query(15, ge=1, le=50)):
    """Archetype 07: Cross-Crime Organised Syndicate Bridge Entities."""
    return {"archetype": "07 - Cross-Crime Syndicate", "bridges": cached_bridges[:top_k]}


@app.get("/api/analytics/anomalies")
def get_anomalies(top_k: int = Query(20, ge=1, le=50)):
    """Archetype 05: Financial Crime & Money Laundering Structuring Anomalies."""
    return {"archetype": "05 - Financial Crime & Laundering", "anomalies": cached_anomalies[:top_k]}


@app.get("/api/lenses")
def get_crime_lenses():
    """Returns the 7 Crime Archetype definitions."""
    return [
        {
            "id": "01",
            "name": "Illicit Supply & Distribution",
            "icon": "📦",
            "pattern": "Supplier → Wholesaler → Broker → Distributor",
            "focus_relations": ["COMMUNICATED_WITH", "EXCHANGED_ITEM_WITH", "MOVED_WITH"]
        },
        {
            "id": "02",
            "name": "Human Trafficking & Exploitation",
            "icon": "👥",
            "pattern": "Recruiter → Transporter → Location → Site",
            "focus_relations": ["MOVED_WITH", "MET_WITH", "PRESENT_AT"]
        },
        {
            "id": "03",
            "name": "Cyber Coercion & Extortion",
            "icon": "💻",
            "pattern": "Victim → Account → Operator → Wallet",
            "focus_relations": ["COMMUNICATED_WITH", "TRANSFERRED_TO"]
        },
        {
            "id": "04",
            "name": "Property Crime & Fencing",
            "icon": "🚗",
            "pattern": "Theft → Vehicle/Item → Fencer → Resale",
            "focus_relations": ["OWNS_VEHICLE", "USED_VEHICLE_WITH", "PRESENT_AT"]
        },
        {
            "id": "05",
            "name": "Financial Crime & Money Laundering",
            "icon": "💳",
            "pattern": "A —₹50K→ B —₹48K→ C —₹49K→ D (Layering)",
            "focus_relations": ["TRANSFERRED_TO", "OWNS_ACCOUNT"]
        },
        {
            "id": "06",
            "name": "Online Coordination & Dissemination",
            "icon": "🌐",
            "pattern": "Account → Content → Burst Communication",
            "focus_relations": ["COMMUNICATED_WITH", "USES_PHONE"]
        },
        {
            "id": "07",
            "name": "Cross-Crime Organised Syndicate",
            "icon": "🕸️",
            "pattern": "Cross-domain high-betweenness broker",
            "focus_relations": ["ALL"]
        }
    ]


@app.get("/api/lenses/{lens_id}")
def get_lens_subgraph(lens_id: str):
    """Returns a filtered graph view specifically tailored for one of the 7 crime lenses."""
    if not tkg:
        raise HTTPException(status_code=503, detail="Engine initializing")

    # Map lens ID to representative focus suspects or relations
    lens_map = {
        "01": {"seed": "P00561", "relations": {"COMMUNICATED_WITH", "EXCHANGED_ITEM_WITH", "PRESENT_AT"}},
        "02": {"seed": "P00151", "relations": {"MET_WITH", "MOVED_WITH", "PRESENT_AT"}},
        "03": {"seed": "P00811", "relations": {"COMMUNICATED_WITH", "USES_PHONE", "OWNS_ACCOUNT"}},
        "04": {"seed": "P00802", "relations": {"OWNS_VEHICLE", "USED_VEHICLE_WITH", "PRESENT_AT"}},
        "05": {"seed": "P00528", "relations": {"TRANSFERRED_TO", "OWNS_ACCOUNT"}},
        "06": {"seed": "P00391", "relations": {"COMMUNICATED_WITH", "USES_PHONE"}},
        "07": {"seed": cached_bridges[0]["entity_id"] if cached_bridges else "P00072", "relations": None}
    }

    config = lens_map.get(lens_id, lens_map["07"])
    sub = tkg.get_subgraph(config["seed"], hops=2, allowed_relations=config["relations"])
    return {
        "lens_id": lens_id,
        "seed_entity": config["seed"],
        "graph": tkg.to_cytoscape_json(sub)
    }


class IngestRequest(BaseModel):
    text: str
    record_id: Optional[str] = None
    language: Optional[str] = None


@app.post("/api/ingest")
def ingest_text_record(payload: IngestRequest):
    """
    Real-Time Multilingual NLP Ingestion:
    Accepts raw police FIR / intercept text in English, Hindi, Urdu, Tamil, etc.,
    extracts the crime event, dynamically adds new nodes & edges into the graph,
    and returns the explainable lead + updated subgraph!
    """
    if not tkg or not extractor:
        raise HTTPException(status_code=503, detail="Engine initializing")

    rec_id = payload.record_id or f"LIVE_{int(os.urandom(3).hex(), 16)}"
    event = extractor.extract_event(rec_id, payload.text, language=payload.language)
    edges = extractor.to_graph_edges(event)

    # Dynamically inject new event and edges into live Knowledge Graph
    for e in edges:
        u = e["head"]
        v = e["tail"]
        if not tkg.graph.has_node(u):
            tkg.graph.add_node(u, entity_type="Person" if u.startswith("P") else "Entity", label=u)
        if not tkg.graph.has_node(v):
            tkg.graph.add_node(v, entity_type="Person" if v.startswith("P") else "Entity", label=v)

        tkg.graph.add_edge(
            u,
            v,
            relation=e["relation"],
            timestamp=e["timestamp"],
            confidence=e["confidence"],
            source_id=e["source_id"],
            event_type=e.get("event_type", "")
        )

    # Extract 1-hop subgraph around primary subject
    center_id = event["subject_person_id"] or (edges[0]["head"] if edges else "P00561")
    sub = tkg.get_subgraph(center_id, hops=2)

    return {
        "status": "success",
        "extracted_event": event,
        "new_edges_count": len(edges),
        "edges": edges,
        "center_entity": center_id,
        "subgraph": tkg.to_cytoscape_json(sub),
        "message": f"Successfully ingested event '{event['event_type']}' and inserted {len(edges)} live graph edges."
    }


# Mount Static Files (Frontend Web Dashboard)
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
