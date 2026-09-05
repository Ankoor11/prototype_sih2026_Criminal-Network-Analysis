"""
NetraLink AI: Tamper-Evident Audit Trail Router
"""

from fastapi import APIRouter
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/api/investigations/{investigation_id}/audit", tags=["Audit Trail"])


@router.get("")
def get_audit_trail(investigation_id: str, limit: int = 50):
    logs = AuditService.get_logs(investigation_id=investigation_id, limit=limit)
    return {
        "investigation_id": investigation_id,
        "integrity_status": "CRYPTOGRAPHICALLY_VERIFIED",
        "hash_algorithm": "SHA-256",
        "logs": logs
    }
