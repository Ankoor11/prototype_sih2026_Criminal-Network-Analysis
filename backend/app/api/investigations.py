"""
NetraLink AI: Investigations Management Router
"""

import json
import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.database.db import get_db_connection
from backend.app.services.audit_service import AuditService
from backend.app.database.demo_seed import seed_demo_case

router = APIRouter(prefix="/api/investigations", tags=["Investigations"])


class InvestigationCreate(BaseModel):
    title: str
    case_number: str
    description: str = ""
    primary_lens: str = "07"
    additional_lenses: List[str] = ["01", "05"]
    threat_level: str = "ELEVATED"


@router.get("")
def list_investigations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investigations ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]

    # Enrich with dynamic counts
    for inv in rows:
        cursor.execute("SELECT COUNT(*) FROM evidence_records WHERE investigation_id = ?", (inv["id"],))
        inv["evidence_count"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM explainable_leads WHERE investigation_id = ?", (inv["id"],))
        inv["leads_count"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE investigation_id = ?", (inv["id"],))
        inv["alerts_count"] = cursor.fetchone()[0]
        if isinstance(inv.get("additional_lenses"), str):
            try:
                inv["additional_lenses"] = json.loads(inv["additional_lenses"])
            except Exception:
                inv["additional_lenses"] = []

    conn.close()
    return {"investigations": rows}


@router.post("")
def create_investigation(payload: InvestigationCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    inv_id = f"INV-{uuid.uuid4().hex[:6].upper()}"
    cursor.execute("""
    INSERT INTO investigations (id, title, case_number, description, primary_lens, additional_lenses, threat_level)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        inv_id,
        payload.title,
        payload.case_number,
        payload.description,
        payload.primary_lens,
        json.dumps(payload.additional_lenses),
        payload.threat_level
    ))
    conn.commit()
    conn.close()

    AuditService.log_event(
        action="INVESTIGATION_CREATED",
        details=f"Created investigation '{payload.title}' ({payload.case_number}) with Primary Lens {payload.primary_lens}.",
        investigation_id=inv_id,
        target_entity=inv_id
    )

    return {"status": "success", "id": inv_id, "case_number": payload.case_number}


@router.get("/{id}")
def get_investigation_details(id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investigations WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Investigation not found.")

    inv = dict(row)
    cursor.execute("SELECT COUNT(*) FROM evidence_records WHERE investigation_id = ?", (id,))
    inv["evidence_count"] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM explainable_leads WHERE investigation_id = ?", (id,))
    inv["leads_count"] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE investigation_id = ?", (id,))
    inv["alerts_count"] = cursor.fetchone()[0]

    if isinstance(inv.get("additional_lenses"), str):
        try:
            inv["additional_lenses"] = json.loads(inv["additional_lenses"])
        except Exception:
            inv["additional_lenses"] = []

    conn.close()
    return inv


@router.post("/{id}/demo-seed")
def seed_demo_investigation(id: str):
    seeded_id = seed_demo_case()
    return {"status": "success", "investigation_id": seeded_id, "message": "Demo investigation 'Operation Eclipse' loaded successfully."}
