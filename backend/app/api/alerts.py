"""
NetraLink AI: Prioritized Alerts Management Router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.database.db import get_db_connection
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/api", tags=["Alerts"])


class AlertStatusUpdate(BaseModel):
    status: str  # UNDER_REVIEW, ACCEPTED, DISMISSED
    user_name: str = "Insp. A. K. Singh"


@router.get("/investigations/{investigation_id}/alerts")
def get_alerts(investigation_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM alerts WHERE investigation_id = ? ORDER BY 
        CASE priority 
            WHEN 'HIGH' THEN 1 
            WHEN 'MEDIUM' THEN 2 
            WHEN 'LOW' THEN 3 
        END, created_at DESC
    """, (investigation_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"alerts": rows}


@router.post("/alerts/{id}/status")
def update_alert_status(id: str, payload: AlertStatusUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET status = ? WHERE id = ?", (payload.status.upper(), id))
    conn.commit()
    conn.close()

    AuditService.log_event(
        action=f"ALERT_STATUS_{payload.status.upper()}",
        details=f"Alert {id} status changed to {payload.status.upper()}.",
        user_name=payload.user_name,
        target_entity=id
    )

    return {"status": "success", "alert_id": id, "new_status": payload.status.upper()}
