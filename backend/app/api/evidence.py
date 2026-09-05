"""
NetraLink AI: Evidence Records Management Router
"""

import hashlib
import json
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.database.db import get_db_connection
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/api/investigations/{investigation_id}/evidence", tags=["Evidence"])


class EvidenceIngestRequest(BaseModel):
    evidence_type: str = "FIR / Police Narrative"
    source_reference: str = "FIR-LIVE-01"
    title: str = "Live Field Intercept"
    content_text: str
    metadata: Optional[dict] = None


@router.get("")
def list_evidence(investigation_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM evidence_records WHERE investigation_id = ? ORDER BY created_at DESC
    """, (investigation_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    for r in rows:
        if isinstance(r.get("metadata_json"), str):
            try:
                r["metadata"] = json.loads(r["metadata_json"])
            except Exception:
                r["metadata"] = {}
    conn.close()
    return {"evidence_records": rows}


@router.post("")
def ingest_evidence(investigation_id: str, payload: EvidenceIngestRequest):
    content = payload.content_text.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Evidence text cannot be empty.")

    ev_id = f"EV-{uuid.uuid4().hex[:6].upper()}"
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    meta_json = json.dumps(payload.metadata or {"source": "Manual Ingestion"})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO evidence_records (id, investigation_id, evidence_type, source_reference, title, content_text, metadata_json, sha256_hash)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ev_id,
        investigation_id,
        payload.evidence_type,
        payload.source_reference,
        payload.title,
        content,
        meta_json,
        sha256
    ))
    conn.commit()
    conn.close()

    AuditService.log_event(
        action="EVIDENCE_INGESTED",
        details=f"Ingested evidence record '{payload.source_reference}' ({payload.evidence_type}). SHA-256 Hash: {sha256[:16]}...",
        investigation_id=investigation_id,
        target_entity=ev_id
    )

    return {
        "status": "success",
        "evidence_id": ev_id,
        "source_reference": payload.source_reference,
        "sha256_hash": sha256,
        "message": "Evidence record securely stored and hashed."
    }
