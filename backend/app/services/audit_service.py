"""
NetraLink AI: Tamper-Evident Audit Logging Service
Generates cryptographic SHA-256 event hashes for chain-of-custody and investigator accountability.
"""

import hashlib
import json
import uuid
from datetime import datetime
from backend.app.database.db import get_db_connection


class AuditService:
    @staticmethod
    def compute_hash(payload: dict) -> str:
        """Computes a canonical SHA-256 hash of the audit entry payload."""
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    @classmethod
    def log_event(
        cls,
        action: str,
        details: str,
        user_name: str = "Insp. A. K. Singh",
        user_role: str = "Senior Investigator",
        investigation_id: str = "INV-001",
        target_entity: str = None
    ) -> dict:
        """Records an immutable audit event in SQLite."""
        event_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        entry_data = {
            "id": event_id,
            "investigation_id": investigation_id,
            "user_name": user_name,
            "user_role": user_role,
            "action": action,
            "target_entity": target_entity or "SYSTEM",
            "details": details,
            "timestamp": ts
        }

        event_hash = cls.compute_hash(entry_data)
        entry_data["event_hash"] = event_hash

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (id, investigation_id, user_name, user_role, action, target_entity, details, event_hash, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, investigation_id, user_name, user_role, action, target_entity, details, event_hash, ts))
        conn.commit()
        conn.close()

        return entry_data

    @staticmethod
    def get_logs(investigation_id: str = None, limit: int = 50) -> list:
        conn = get_db_connection()
        cursor = conn.cursor()
        if investigation_id:
            cursor.execute("""
                SELECT * FROM audit_logs WHERE investigation_id = ? ORDER BY timestamp DESC LIMIT ?
            """, (investigation_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
