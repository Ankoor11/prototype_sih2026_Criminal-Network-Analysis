"""
Test script to verify all NetraLink FastAPI backend endpoints.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from netralink.server.app import app, initialize_engine


def test_all_endpoints():
    print("=" * 65)
    print("   TESTING NETRALINK BACKEND API ENDPOINTS")
    print("=" * 65)

    initialize_engine()
    client = TestClient(app)

    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    print("[OK] GET /api/health:", res.json())

    # 2. Graph Stats
    res = client.get("/api/graph/stats")
    assert res.status_code == 200
    stats = res.json()
    print(f"[OK] GET /api/graph/stats: {stats['total_nodes']:,} nodes, {stats['total_edges']:,} edges")

    # 3. Syndicate Bridges (Archetype 07)
    res = client.get("/api/analytics/bridge-entities?top_k=3")
    assert res.status_code == 200
    bridges = res.json()["bridges"]
    print(f"[OK] GET /api/analytics/bridge-entities: Found {len(bridges)} top brokers.")
    for b in bridges[:2]:
        print(f"   * {b['entity_id']}: {b['label']} (Bridge Score: {b['bridge_score']*100:.1f}%)")

    # 4. Financial Anomalies (Archetype 05)
    res = client.get("/api/analytics/anomalies?top_k=3")
    assert res.status_code == 200
    anomalies = res.json()["anomalies"]
    print(f"[OK] GET /api/analytics/anomalies: Found {len(anomalies)} suspicious flows.")

    # 5. Crime Lens 07
    res = client.get("/api/lenses/07")
    assert res.status_code == 200
    lens_data = res.json()
    print(f"[OK] GET /api/lenses/07: Loaded seed {lens_data['seed_entity']} with {len(lens_data['graph']['nodes'])} nodes.")

    # 6. Live Multilingual Text Ingestion (POST /api/ingest)
    sample_hindi = "PERSON_00151 और PERSON_00985 ने मिला, Zone_0178, Gwalior के पास। समय 2026-04-05 11:39:00."
    res = client.post("/api/ingest", json={"text": sample_hindi, "language": "hi"})
    assert res.status_code == 200
    ingest_data = res.json()
    print("[OK] POST /api/ingest (Hindi):", ingest_data["message"])
    print(f"   • Event: {ingest_data['extracted_event']['event_type']} (Confidence: {ingest_data['extracted_event']['confidence']*100}%)")
    print(f"   • New Graph Edges Created: {ingest_data['new_edges_count']}")

    print("\n" + "=" * 65)
    print("   ALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    test_all_endpoints()
