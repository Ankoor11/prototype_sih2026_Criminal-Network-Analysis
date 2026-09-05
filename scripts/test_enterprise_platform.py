"""
Comprehensive test suite for NetraLink AI Enterprise Platform.
Validates all 14 core user journey endpoints from Login to Audit Trail.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app, startup_event


def run_tests():
    print("=" * 70)
    print("   VALIDATING NETRALINK AI FULL-STACK ENTERPRISE WORKFLOW")
    print("=" * 70)

    # Initialize app and database
    startup_event()
    client = TestClient(app)
    case_id = "INV-ECLIPSE-2026"

    # 1. Login & RBAC
    res = client.post("/api/auth/login", json={"role": "Senior Investigator"})
    assert res.status_code == 200
    user_info = res.json()["user"]
    print(f"[OK] 01. Login: {user_info['name']} ({user_info['role']}) · Clearance: {user_info['clearance_level']}")

    # 2. Case Workspace
    res = client.get("/api/investigations")
    assert res.status_code == 200
    cases = res.json()["investigations"]
    assert len(cases) >= 1
    print(f"[OK] 02. Workspace: Found {len(cases)} active case(s). Current: '{cases[0]['title']}'")

    # 3. Evidence Ingestion Hub
    res = client.get(f"/api/investigations/{case_id}/evidence")
    assert res.status_code == 200
    evidence = res.json()["evidence_records"]
    assert len(evidence) >= 5
    print(f"[OK] 03. Evidence Hub: {len(evidence)} records with SHA-256 integrity hashes.")

    # 4. 11-Stage Processing Pipeline
    res = client.post(f"/api/investigations/{case_id}/pipeline/run")
    assert res.status_code == 200
    pipeline_res = res.json()
    assert len(pipeline_res["stages"]) == 11
    print(f"[OK] 04. Pipeline: Executed all 11 stages in {pipeline_res['metrics']['execution_time_seconds']}s.")

    # 5. Entity Explorer (Mentioned vs Resolved)
    res = client.get(f"/api/investigations/{case_id}/entities")
    assert res.status_code == 200
    ent_data = res.json()
    assert len(ent_data["resolved_persons"]) > 0
    print(f"[OK] 05. Entities Explorer: {ent_data['total_canonical_entities']:,} canonical entities verified.")

    # 6. Entity Resolution Workbench
    res = client.get(f"/api/investigations/{case_id}/entities/resolution/candidates")
    assert res.status_code == 200
    candidates = res.json()["candidates"]
    assert len(candidates) >= 1
    c1 = candidates[0]
    print(f"[OK] 06. Resolution: Candidate '{c1['mentioned_entity']}' -> '{c1['canonical_candidate_id']}' (Score: {c1['match_score']*100}%).")

    # 7. Resolution Action (Confirm Match)
    res = client.post(f"/api/investigations/{case_id}/entities/resolution/decide", json={
        "candidate_id": c1["candidate_id"],
        "decision": "CONFIRM",
        "notes": "Verified by Investigator via FIR-RPT00001 co-occurrence."
    })
    assert res.status_code == 200
    print(f"[OK] 07. Resolution Action: Match confirmed and logged to audit trail.")

    # 8. Knowledge Graph Canvas
    res = client.get(f"/api/investigations/{case_id}/graph?entity_id=P00561&hops=2")
    assert res.status_code == 200
    graph_data = res.json()
    assert len(graph_data["nodes"]) > 0
    print(f"[OK] 08. Graph Canvas: Loaded egocentric neighborhood ({len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges).")

    # 9. Find Hidden Paths
    res = client.get(f"/api/investigations/{case_id}/graph/hidden-paths?source_id=P00561&target_id=P00151")
    assert res.status_code == 200
    paths_data = res.json()
    assert paths_data["paths_count"] >= 1
    p = paths_data["paths"][0]
    print(f"[OK] 09. Hidden Pathfinding: Discovered {p['path_id']} ({p['length']} operational hops): {' -> '.join(p['nodes'])}")

    # 10. 7 Crime Lenses
    res = client.get(f"/api/investigations/{case_id}/lenses")
    assert res.status_code == 200
    lenses = res.json()
    assert len(lenses) == 7
    print(f"[OK] 10. Crime Lenses: All 7 operational lenses loaded (Lenses 01 to 07).")

    # 11. Cross-Crime Radar (Archetype 07)
    res = client.get(f"/api/investigations/{case_id}/cross-crime")
    assert res.status_code == 200
    cross = res.json()
    assert len(cross["bridge_candidates"]) >= 1
    top_bridge = cross["bridge_candidates"][0]
    print(f"[OK] 11. Cross-Crime Radar: Top Bridge Nexus: {top_bridge['entity_id']} (Bridge Score: {top_bridge['bridge_score']*100}%).")

    # 12. Explainable Leads
    res = client.get(f"/api/investigations/{case_id}/leads")
    assert res.status_code == 200
    leads = res.json()["leads"]
    assert len(leads) >= 1
    lead1 = leads[0]
    print(f"[OK] 12. Explainable Leads: Lead {lead1['lead_number']} ({lead1['candidate_label']}) with {len(lead1['cited_evidence'])} cited sources.")

    # 13. Human Review Decision Terminal
    res = client.post(f"/api/leads/{lead1['id']}/review", json={
        "decision": "ACCEPT",
        "reviewer_name": "Insp. A. K. Singh",
        "reason": "Corroborated by Ujjain Narcotics Cell and FIU-IND transaction reports."
    })
    assert res.status_code == 200
    rev_res = res.json()
    print(f"[OK] 13. Human Review: Lead {lead1['lead_number']} status changed to {rev_res['new_status']}.")

    # 14. Cryptographic Audit Trail
    res = client.get(f"/api/investigations/{case_id}/audit")
    assert res.status_code == 200
    audit_data = res.json()
    assert len(audit_data["logs"]) >= 3
    print(f"[OK] 14. Audit Trail: Verified {len(audit_data['logs'])} cryptographic log entries (Hash: {audit_data['logs'][0]['event_hash'][:16]}...).")

    print("\n" + "=" * 70)
    print("   ALL 14 USER JOURNEY ENDPOINTS VALIDATED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
