"""
NetraLink AI: Demonstration Case Seeder ("Operation Eclipse")
Seeds an internally consistent, synthetic multi-jurisdictional investigation dossier.
"""

import os
import sys
import json
import hashlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from backend.app.database.db import get_db_connection, init_db
from backend.app.services.audit_service import AuditService


def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def seed_demo_case():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    inv_id = "INV-ECLIPSE-2026"

    # 1. Check if already seeded
    cursor.execute("SELECT id FROM investigations WHERE id = ?", (inv_id,))
    if cursor.fetchone():
        conn.close()
        print(f"[Seeder] Investigation '{inv_id}' is already seeded.")
        return inv_id

    # 2. Insert Master Investigation
    cursor.execute("""
    INSERT INTO investigations (id, title, case_number, description, primary_lens, additional_lenses, status, threat_level, lead_investigator)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inv_id,
        "Operation Eclipse: Cross-State Syndicate Nexus",
        "CR-2026-MP-0482",
        "Multi-agency probe investigating cross-border narcotics trafficking, Hawala layering under ₹50K thresholds, vehicle resale rings, and cyber extortion coordination.",
        "07",
        json.dumps(["01", "03", "04", "05"]),
        "ACTIVE",
        "CRITICAL",
        "Insp. A. K. Singh (Special Crime Branch)"
    ))

    # 3. Seed Ingested Evidence Records
    evidence_items = [
        {
            "id": "EV-FIR-101",
            "type": "FIR / Police Narrative",
            "ref": "FIR-RPT00001",
            "title": "Initial Observation Report: Zone 123 Ujjain",
            "text": "On 2026-07-25, the record noted that PERSON_00561 was observed with PERSON_00975 near Zone_0123 in Ujjain. The note references phone PH01018, account ACC00481, and vehicle VEH00359. Available records indicate activity within the surrounding time window. Additional communication, location and transaction records may be reviewed to determine whether the entities are connected.",
            "meta": {"language": "en", "jurisdiction": "Ujjain Central PS", "officer": "SI Verma"}
        },
        {
            "id": "EV-CDR-204",
            "type": "Telecom CDR Log",
            "ref": "CDR-000001",
            "title": "Telecom Intercept: Communication Burst",
            "text": "CDR Record CDR000001: Phone PH01018 initiated call to PH00673 (Duration: 1717 sec, Channel: Cellular Voice, Cell Tower: LOC0042, Timestamp: 2026-01-08 09:54:00). High frequency burst recorded prior to shipment movement.",
            "meta": {"carrier": "Airtel/Jio Cell Grid", "cell_id": "TOWER_042"}
        },
        {
            "id": "EV-BNK-309",
            "type": "Banking Transaction Record",
            "ref": "TX-000235",
            "title": "Suspicious Structuring Transfer",
            "text": "Transaction TX000235: Immediate Online IMPS Transfer of ₹64,515.97 from Current Account ACC00042 to Current Account ACC00481 (Beneficiary: P00561). Flagged with amount z-score +3.16. Rapid layering observed into mule account ACC01174 within 3 hours.",
            "meta": {"bank": "National Financial Switch", "flag": "FIU-IND STR TRIGGER"}
        },
        {
            "id": "EV-GEO-412",
            "type": "Geospatial Surveillance Trace",
            "ref": "GEO-000001",
            "title": "Safehouse Co-Location Ping",
            "text": "Geo-Fence Alert GEO000001: Person P00561 logged entering commercial warehouse at Zone_0140 (Jabalpur Sector 4) at 2026-06-29 08:35:00. Confidence rating: 0.81.",
            "meta": {"sensor": "Automated License Plate & Cell Tower Triangulation"}
        },
        {
            "id": "EV-INT-505",
            "type": "Multilingual Intercept",
            "ref": "INT-HINDI-02",
            "title": "Field Surveillance Intercept (Hindi)",
            "text": "PERSON_00151 और PERSON_00985 ने मिला, Zone_0178, Gwalior के पास। समय 2026-04-05 11:39:00. गुप्त बैठक में नकदी और पार्सल के आदान-प्रदान की सूचना दर्ज की गई।",
            "meta": {"language": "hi", "intercept_unit": "Special Task Force"}
        }
    ]

    for ev in evidence_items:
        cursor.execute("""
        INSERT INTO evidence_records (id, investigation_id, evidence_type, source_reference, title, content_text, metadata_json, sha256_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ev["id"],
            inv_id,
            ev["type"],
            ev["ref"],
            ev["title"],
            ev["text"],
            json.dumps(ev["meta"]),
            hash_content(ev["text"])
        ))

    # 4. Seed Explainable Leads
    cursor.execute("""
    INSERT INTO explainable_leads (id, investigation_id, lead_number, title, priority, lead_type, candidate_entity_id, candidate_label, bridge_score, explanation_points, cited_evidence, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "LEAD-001",
        inv_id,
        "NL-0017",
        "Cross-Crime Bridge Nexus: Rahul Sharma @ Guddu",
        "HIGH",
        "Cross-Crime Organised Syndicate Bridge",
        "P00561",
        "Rahul Sharma @ Guddu",
        0.89,
        json.dumps([
            "Rahul Sharma @ Guddu is directly linked to primary device Phone PH01018 observed in 14 telecom bursts.",
            "Phone PH01018 logged recurrent direct calls with known narcotics wholesaler Deepak Verma.",
            "Subject owns Current Account ACC00481 which received 3 structured transfers totaling ₹1,48,500 under statutory reporting limits.",
            "Funds in ACC00481 were layered within 3 hours into mule account ACC01174, characteristic of Hawala laundering.",
            "Subject was observed operating Vehicle VEH00359 (White SUV) co-located near reported property theft fencing site Zone 123.",
            "Subject's Network Participation Coefficient reveals connectivity across 4 distinct operational clusters: Drug Supply, Hawala Laundering, Vehicle Theft, and Cyber Extortion.",
            "Temporal correlation shows overlapping activity windows between January 2026 and August 2026."
        ]),
        json.dumps(["FIR-RPT00001", "CDR-000001", "TX-000235", "GEO-000001"]),
        "UNDER_REVIEW"
    ))

    # 5. Seed Prioritized Alerts
    alerts = [
        ("ALT-01", "Cross-Crime Syndicate Bridge", "HIGH", "P00561", "High-Betweenness Bridge Entity Detected", "Rahul Sharma @ Guddu actively bridges Narcotics Supply and Hawala Financial clusters with Bridge Score 0.89.", 4),
        ("ALT-02", "Financial Structuring / Layering", "HIGH", "ACC00481", "Rapid Multi-Hop Laundering Chain", "Account ACC00481 received structured funds rapidly moved to mule account ACC01174.", 2),
        ("ALT-03", "Communication Burst", "MEDIUM", "PH01018", "Pre-Incident Telecom Spike", "14 calls recorded within 48 hours preceding narcotics shipment movement.", 1),
        ("ALT-04", "Alias Resolution Conflict", "LOW", "P00561", "Potential Alias Match Available", "Candidate identity match 'Rahul Kumar Sharma' identified with 94.2% semantic similarity.", 1)
    ]
    for alt_id, atype, prio, ent, title, desc, cnt in alerts:
        cursor.execute("""
        INSERT INTO alerts (id, investigation_id, alert_type, priority, entity_id, title, description, evidence_count, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'NEW')
        """, (alt_id, inv_id, atype, prio, ent, title, desc, cnt))

    conn.commit()
    conn.close()

    # 6. Audit Trail Initialization
    AuditService.log_event(
        action="INVESTIGATION_INITIALIZED",
        details="Seeded canonical multi-agency dossier 'Operation Eclipse' with 5 source records and 4 cross-crime alerts.",
        investigation_id=inv_id,
        target_entity="INV-ECLIPSE-2026"
    )

    print(f"[Seeder] Successfully seeded 'Operation Eclipse' ({inv_id})")
    return inv_id


if __name__ == "__main__":
    seed_demo_case()
