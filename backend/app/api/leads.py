"""
NetraLink AI: Explainable Leads & Human Review Decision Router
"""

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.database.db import get_db_connection
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/api", tags=["Leads & Human Review"])


class LeadReviewDecision(BaseModel):
    decision: str  # ACCEPT, DISMISS, FLAG
    reviewer_name: str = "Insp. A. K. Singh"
    reason: str


@router.get("/investigations/{investigation_id}/leads")
def get_leads(investigation_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM explainable_leads WHERE investigation_id = ? ORDER BY created_at DESC
    """, (investigation_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    for r in rows:
        if isinstance(r.get("explanation_points"), str):
            try:
                r["explanation_points"] = json.loads(r["explanation_points"])
            except Exception:
                r["explanation_points"] = []
        if isinstance(r.get("cited_evidence"), str):
            try:
                r["cited_evidence"] = json.loads(r["cited_evidence"])
            except Exception:
                r["cited_evidence"] = []
    conn.close()
    return {"leads": rows}


@router.post("/leads/{id}/review")
def review_lead(id: str, payload: LeadReviewDecision):
    if not payload.reason.strip():
        raise HTTPException(status_code=400, detail="Investigator must provide rationale for decision.")

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM explainable_leads WHERE id = ?", (id,))
    lead = cursor.fetchone()
    if not lead:
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found.")

    lead_dict = dict(lead)
    new_status = f"{payload.decision.upper()}ED" if payload.decision.upper() in ["ACCEPT", "DISMISS"] else "FLAGGED"

    cursor.execute("""
    UPDATE explainable_leads
    SET status = ?, review_notes = ?, reviewed_by = ?, reviewed_at = ?
    WHERE id = ?
    """, (new_status, payload.reason, payload.reviewer_name, ts, id))
    conn.commit()
    conn.close()

    # Log immutable audit event
    AuditService.log_event(
        action=f"LEAD_REVIEW_{new_status}",
        details=f"Lead {lead_dict['lead_number']} ({lead_dict['candidate_label']}) was {new_status.lower()} by {payload.reviewer_name}. Rationale: '{payload.reason}'.",
        user_name=payload.reviewer_name,
        investigation_id=lead_dict["investigation_id"],
        target_entity=lead_dict["candidate_entity_id"]
    )

    return {
        "status": "success",
        "lead_id": id,
        "new_status": new_status,
        "reviewed_by": payload.reviewer_name,
        "timestamp": ts,
        "message": f"Lead {lead_dict['lead_number']} status updated to {new_status} and cryptographically audited."
    }
