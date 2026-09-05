"""
NetraLink AI: SQLite Relational Database Layer
Handles persistent storage for Investigations, Evidence Records, Explainable Leads, Alerts, and Audit Logs.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "netralink.db"))


def get_db_connection():
    """Returns a connection with Row factory enabled for dictionary-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes all required schema tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Investigations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS investigations (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        case_number TEXT UNIQUE NOT NULL,
        description TEXT,
        primary_lens TEXT NOT NULL,
        additional_lenses TEXT,
        status TEXT DEFAULT 'ACTIVE',
        threat_level TEXT DEFAULT 'ELEVATED',
        lead_investigator TEXT DEFAULT 'Insp. A. K. Singh',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Evidence Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence_records (
        id TEXT PRIMARY KEY,
        investigation_id TEXT NOT NULL,
        evidence_type TEXT NOT NULL,
        source_reference TEXT NOT NULL,
        title TEXT,
        content_text TEXT,
        metadata_json TEXT,
        sha256_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(investigation_id) REFERENCES investigations(id)
    );
    """)

    # 3. Explainable Leads Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS explainable_leads (
        id TEXT PRIMARY KEY,
        investigation_id TEXT NOT NULL,
        lead_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        priority TEXT NOT NULL,
        lead_type TEXT NOT NULL,
        candidate_entity_id TEXT NOT NULL,
        candidate_label TEXT NOT NULL,
        bridge_score REAL DEFAULT 0.0,
        explanation_points TEXT NOT NULL,
        cited_evidence TEXT NOT NULL,
        status TEXT DEFAULT 'UNDER_REVIEW',
        review_notes TEXT,
        reviewed_by TEXT,
        reviewed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(investigation_id) REFERENCES investigations(id)
    );
    """)

    # 4. Alerts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        investigation_id TEXT NOT NULL,
        alert_type TEXT NOT NULL,
        priority TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        evidence_count INTEGER DEFAULT 1,
        status TEXT DEFAULT 'NEW',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(investigation_id) REFERENCES investigations(id)
    );
    """)

    # 5. Tamper-Evident Audit Trail Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        investigation_id TEXT,
        user_name TEXT NOT NULL,
        user_role TEXT NOT NULL,
        action TEXT NOT NULL,
        target_entity TEXT,
        details TEXT NOT NULL,
        event_hash TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print(f"[Database] SQLite schema verified at {DB_PATH}")


if __name__ == "__main__":
    init_db()
