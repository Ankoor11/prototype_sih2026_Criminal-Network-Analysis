# NetraLink AI: Law Enforcement Intelligence Platform

> **"Seven lenses. One graph. One evidence trail."**  
> *NetraLink doesn't just identify entities. It connects people, assets, events, locations, and money across fragmented records and explains why a relationship matters.*

---

## 1. Quickstart (One-Command Startup)

The system is **100% self-contained and offline-ready**. It runs entirely on your local machine with **zero external cloud API dependencies or paid keys**:

```bash
# In this workspace directory:
python run_app.py
```

This will automatically:
1. Initialize the SQLite relational database and seed the canonical **"Operation Eclipse"** demonstration case.
2. Load the **3,980 entity nodes** and **56,750 evidence edges** into the Temporal Knowledge Graph.
3. Start the FastAPI REST server on `http://127.0.0.1:8000`.
4. **Open the interactive Investigative Dashboard directly in your default web browser.**

---

## 2. The 5–10 Minute Demonstration Script (For Presentation Panels)

Walk judges through this exact end-to-end investigator journey:

1. **Login & RBAC Profile** (`/`):
   - Authenticated as `Insp. A. K. Singh` (Role: **Senior Investigator**, Level 4 National Clearance).
2. **Investigation Workspace** (`Overview` tab):
   - Active Case: **Operation Eclipse: Cross-State Syndicate Nexus** (`CR-2026-MP-0482`).
   - Threat Level: `CRITICAL THREAT`.
   - Metrics: 5 Evidence records, 3,980 nodes, 56,750 edges, 1 flagged cross-crime bridge.
3. **Evidence Ingestion Hub** (`Evidence Hub` tab):
   - Review primary sources: FIR observation narrative, Telecom CDR burst, Structuring bank transfer, Geospatial trace.
   - Note the **SHA-256 evidence integrity hashes** establishing chain-of-custody.
4. **11-Stage Intelligence Pipeline** (`11-Stage Pipeline` tab):
   - Click **"Execute Full Pipeline"**.
   - Watch all 11 stages transition from `Evidence Received` $\to$ `Normalization` $\to$ `Multilingual NER` $\to$ `Entity Resolution` $\to$ `Event Extraction` $\to$ `Graph Construction` $\to$ `Crime Lenses` $\to$ `Cross-Crime Discovery` $\to$ `Anomaly Detection` $\to$ `Lead Generation` $\to$ `Human Review`.
5. **Entity Explorer** (`Entities Explorer` tab):
   - Demonstrates the critical difference between **Mentioned Entities** (raw text mentions in FIRs/CDRs) and **Resolved Canonical Entities** (`P00561`, `PH01018`, `ACC00481`).
6. **Entity Resolution Workbench** (`Resolution Workbench` tab):
   - Inspect Candidate Match `RES-001`: `"R. Sharma"` $\leftrightarrow$ `"Rahul Sharma @ Guddu"` (Match Score: **94.0%**).
   - Signals breakdown: Name Levenshtein (0.91), Phone overlap (1.0), Location overlap (0.95).
   - Click **"Confirm Canonical Match"**; the system commits the link and writes an audit log.
7. **Temporal Knowledge Graph** (`Temporal Graph` tab):
   - Subject **Person X (`P00561`)** is centered with blue node color.
   - Connected assets visible: Phone `PH01018` (Green), Account `ACC00481` (Amber), Vehicle `VEH00359` (Purple), Zone `LOC0123` (Red).
   - Click **"Expand 1-Hop / 2-Hop"** to reveal connected associates.
   - Click **"Find Hidden Links"** between `P00561` and `P00151`: reveals associative chain traversing safehouse `LOC0170` and laundering account with operational significance.
8. **7 Crime-Specific Intelligence Lenses** (`7 Crime Lenses` tab):
   - "The crime bucket changes the lens — not the underlying graph."
   - Switch through Supply, Trafficking, Cyber, Property, Laundering, Online Coordination, and Cross-Crime Syndicate.
9. **Cross-Crime Radar (Archetype 07 — "The Difference Maker")** (`Cross-Crime Radar` tab):
   - Shows how `P00561` bridges **Narcotics Supply**, **Hawala Structuring**, **Vehicle Fencing**, and **Cyber Extortion** with a **Bridge Score of 0.89**.
10. **Explainable Lead Terminal** (`Explainable Leads` tab):
    - Inspect Lead **#NL-0017**: 8 numbered, evidence-backed points explaining *why* the subject is a high-priority syndicate broker.
    - Click source citations `[FIR-RPT00001]`, `[CDR-000001]`, `[TX-000235]`.
11. **Human Review Decision Terminal**:
    - AI never decides guilt; investigator reviews finding.
    - Click **"Conduct Human Review"** $\to$ Select **"Accept as Actionable Lead"** $\to$ Enter mandatory legal justification: *"Corroborated by Ujjain Narcotics Cell and FIU-IND transaction reports"*.
12. **Tamper-Evident Audit Trail** (`Audit Trail` tab):
    - Shows the immutable log of every action taken by the investigator with SHA-256 event hashes.

---

## 3. Directory Structure

```
File/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Master FastAPI application & route registration
│   │   ├── api/                     # 11 REST API modules (Auth, Cases, Evidence, Graph, Leads, etc.)
│   │   ├── database/
│   │   │   ├── db.py                # SQLite connection & schema initialization
│   │   │   └── demo_seed.py         # Seeds "Operation Eclipse" dossier
│   │   └── services/
│   │       ├── ai_pipeline.py       # 11-Stage intelligence pipeline runner
│   │       ├── graph_service.py     # Graph neighborhood, hidden paths, entity resolution
│   │       └── audit_service.py     # Cryptographic SHA-256 audit logger
│   └── netralink.db                 # SQLite database file
├── frontend/
│   ├── index.html                   # Multi-view law enforcement dashboard
│   ├── css/
│   │   └── main.css                 # Dark-mode intelligence design system
│   └── js/
│       ├── api.js                   # Typed REST API client
│       └── app.js                   # Master application & Cytoscape controller
├── netralink/
│   ├── nlp/                         # Multilingual Event Extractor & 11 Indic language triggers
│   ├── graph/                       # Temporal Knowledge Graph (56,750 edges)
│   └── analytics/                   # Syndicate Bridge (Archetype 07) & Anomaly detectors
├── scripts/
│   └── test_enterprise_platform.py # Full 14-step automated verification test suite
├── run_app.py                       # Single command master application launcher
└── README.md
```

---

## 4. Verification Suite

Run automated unit and integration tests across the complete platform:

```bash
# Verify all 14 user journey endpoints:
python scripts/test_enterprise_platform.py
```
