# NetraLink AI — Law Enforcement Intelligence Platform

> **Seven lenses. One graph. One evidence trail.**
> NetraLink connects people, assets, events, locations, and money across fragmented records — and explains *why* a relationship matters.

Built as a prototype for **Smart India Hackathon 2026** (Problem Statement: AI-Powered Criminal Network Analysis System).

---

## Table of Contents

- [Overview](#overview)
- [Key Capabilities](#key-capabilities)
- [Tech Stack](#tech-stack)
- [Quickstart](#quickstart)
- [Guided Walkthrough](#guided-walkthrough)
- [Repository Structure](#repository-structure)
- [Verification / Tests](#verification--tests)
- [Ethics & Human-in-the-Loop](#ethics--human-in-the-loop)
- [Disclaimer](#disclaimer)

---

## Overview

NetraLink AI is a self-contained investigative platform that ingests raw case evidence (FIRs, call detail records, bank transactions, geospatial traces, etc.), resolves it into a **temporal knowledge graph** of entities and relationships, and surfaces **explainable, evidence-backed leads** for human investigators to review.

It ships with a fully seeded demonstration case — **"Operation Eclipse"** — a fictional cross-state syndicate investigation, so the platform can be explored end-to-end with no external setup.

**Highlights:**
- 100% local and offline — no cloud APIs or paid keys required
- An 11-stage intelligence pipeline, from raw evidence to human-reviewed leads
- 7 crime-specific analytical lenses over a single underlying graph
- Full chain-of-custody: every evidence item and every action is hashed and logged

## Key Capabilities

| Capability | Description |
|---|---|
| **Temporal Knowledge Graph** | Entities (people, phones, accounts, vehicles, locations) and their relationships, resolved and linked over time. |
| **Entity Resolution Workbench** | Reviews candidate matches (e.g. name/phone/location similarity) and lets an investigator confirm or reject canonical links. |
| **11-Stage Intelligence Pipeline** | Evidence Received → Normalization → Multilingual NER → Entity Resolution → Event Extraction → Graph Construction → Crime Lenses → Cross-Crime Discovery → Anomaly Detection → Lead Generation → Human Review. |
| **7 Crime-Specific Lenses** | Supply, Trafficking, Cyber, Property, Laundering, Online Coordination, and Cross-Crime Syndicate — different views over the same graph. |
| **Cross-Crime Radar** | Detects entities that "bridge" multiple crime types (e.g. narcotics + laundering + fencing) and scores their significance. |
| **Explainable Lead Terminal** | Every generated lead is backed by numbered, source-cited justifications — not a black-box score. |
| **Human Review & Audit Trail** | AI never determines guilt. Every decision requires investigator sign-off with a legal justification, logged with SHA-256 event hashes for tamper-evidence. |

## Tech Stack

NetraLink is a Python-backed, browser-rendered application with no external services, cloud APIs, or paid keys — everything runs on a single local process.

### Backend — Python / FastAPI

- **[FastAPI](https://fastapi.tiangolo.com/)** serves the REST API (`backend/app/main.py`), with routers split by domain: `auth`, `investigations`, `evidence`, `processing`, `entities`, `graph`, `lenses`, `leads`, `alerts`, `map`, and `audit` (`backend/app/api/`).
- **[Uvicorn](https://www.uvicorn.org/)** is the ASGI server (`run_app.py` launches it programmatically on `127.0.0.1:8000`).
- **[Pydantic](https://docs.pydantic.dev/)** models validate request/response payloads (e.g. `LoginRequest`, `EvidenceIngestRequest`).
- FastAPI's `StaticFiles` mount serves the entire `frontend/` directory directly — there's no separate frontend build step or dev server.
- **CORS** is wide open (`allow_origins=["*"]`) since this is a local, single-user prototype.

### Data Layer — SQLite

- The **`sqlite3`** standard-library module (`backend/app/database/db.py`) backs a relational store (`backend/netralink.db`) holding investigations, evidence records, explainable leads, alerts, and audit log entries.
- `backend/app/database/demo_seed.py` seeds the "Operation Eclipse" demo case on every startup.
- No ORM is used — queries are raw SQL via `sqlite3.Row` for dict-like row access.

### Graph Engine — NetworkX

- The Temporal Knowledge Graph (`netralink/graph/temporal_kg.py`) is a **NetworkX `MultiDiGraph`** — chosen specifically to allow multiple, independently timestamped edges between the same pair of nodes (e.g. repeated calls between two phones).
- Nodes are typed entities — `Person`, `Phone`, `Account`, `Vehicle`, `Location`, `Organization` — loaded from CSVs in `dataset/raw/` via **pandas**.
- Structural edges (ownership, residence) and event-derived edges (communications, transfers, meetings) are added on top of the entity backbone.
- `GraphService` (`backend/app/services/graph_service.py`) wraps the graph as an application-wide singleton and exposes hop-based subgraph extraction for the graph explorer UI.

### NLP / Event Extraction — Rule-Based, Not ML

- Event extraction (`netralink/nlp/event_extractor.py`) is a **deterministic, regex-and-trigger-lexicon engine** — there's no spaCy, transformers, or LLM call involved, which keeps it fully offline and its outputs auditable.
- `netralink/nlp/triggers_data.py` defines a multilingual trigger lexicon (English, Hindi, Urdu, Punjabi, Tamil, Kannada, Bengali, Telugu, Gujarati, Malayalam, Marathi) mapped to canonical event types (`communication`, `meeting`, `item_handoff`, `movement`, `transfer`, `vehicle_use`, `account_access`, `observation`).
- Regex patterns extract structured entity references (`P#####`, `PH#####`, `ACC#####`, `VEH#####`, `LOC####`) and ISO-style timestamps directly out of narrative text.
- `triggers.json` at the repo root holds an editable/config version of trigger rules used by the pipeline.

### Analytics Modules

- **Archetype 05 — Financial Anomaly Detector** (`netralink/analytics/financial_anomaly.py`): pandas/NumPy-based detection of structuring and mule-account patterns, joining `dataset/raw/transactions.csv` against precomputed `dataset/labels/anomaly_labels.csv` (amount z-scores and anomaly labels).
- **Archetype 07 — Syndicate Bridge Detector** (`netralink/analytics/syndicate_bridge_detector.py`): builds an undirected projection of the graph and runs **NetworkX community detection + betweenness centrality** to compute a "bridge score" — identifying entities that connect otherwise-separate criminal clusters (the basis of the Cross-Crime Radar).

### Security / Audit Trail

- `AuditService` (`backend/app/services/audit_service.py`) canonically serializes each audit payload (`json.dumps(..., sort_keys=True)`) and hashes it with **SHA-256** (`hashlib`) before writing it to the `audit_log` SQLite table — the basis of the "tamper-evident" chain-of-custody claim.
- **Auth is currently a demo stub** (`backend/app/api/auth.py`): `/api/auth/login` accepts any username/password and returns a fixed investigator profile and a static bearer token. There's no password hashing, JWT verification, or user table yet — worth flagging clearly if this ever moves beyond a hackathon demo.

### Frontend — Vanilla JS, No Framework

- Plain HTML/CSS/JS served as static assets (`frontend/index.html`, `frontend/js/app.js`, `frontend/js/api.js`) — no React/Vue/build tooling.
- **[D3.js v7](https://d3js.org/)** (via CDN) drives the Temporal Knowledge Graph view: `d3.forceSimulation` with link/charge/collide/center forces renders an interactive force-directed graph on an HTML canvas, with `d3.zoom` for pan/zoom.
- **[Leaflet.js 1.9.4](https://leafletjs.com/)** powers the geospatial map view for location-based evidence.
- **[Lucide](https://lucide.dev/)** provides the icon set.
- Fonts are loaded from Google Fonts: Space Grotesk, Inter, and JetBrains Mono.
- *Note:* the repo also contains a legacy `frontend/app.js` that builds its graph with **Cytoscape.js** — it's not referenced by `index.html` and appears superseded by the D3-based `frontend/js/app.js`.

### Dataset

- `dataset/raw/` — synthetic source CSVs (persons, phones, accounts, vehicles, organizations, locations, transactions, communications, geo events, digital records, items, reports, graph edges) underpinning the demo case.
- `dataset/labels/` — precomputed labels for anomaly detection, event classification, NER, and link prediction.
- `dataset/kg/{train,valid,test}.txt` and `dataset/splits/hidden_*.csv` — knowledge-graph triple splits and held-out evaluation sets, in a format typical of KG-embedding benchmarks (no embedding-model training code is present in this repo yet).
- `data/processed/` — precomputed graph edges/events, a sample subgraph in Cytoscape JSON format, and a Neo4j-compatible Cypher schema loader (`load_netralink_schema.cypher`) — groundwork for an optional graph-database backend, not currently wired into the running app.

### Testing

- `netralink/tests/` — `unittest`-based tests for the event extractor and temporal knowledge graph.
- `scripts/test_enterprise_platform.py` and `scripts/test_server_endpoints.py` — end-to-end tests against the running API.

### A note on setup

The repository does not currently include a `requirements.txt` or `pyproject.toml`. Based on the imports across the codebase, the runtime dependencies are:

```
fastapi
uvicorn
pydantic
pandas
numpy
networkx
```

Install with:

```bash
pip install fastapi uvicorn pydantic pandas numpy networkx
```

## Quickstart

**Requirements:** Python 3.x. No external services or API keys needed.

```bash
python run_app.py
```

This single command will:

1. Initialize the local SQLite database and seed the **"Operation Eclipse"** demo case.
2. Load the demo Temporal Knowledge Graph (thousands of entity nodes and evidence-backed edges).
3. Start the FastAPI backend at `http://127.0.0.1:8000`.
4. Open the Investigative Dashboard in your default browser.

## Guided Walkthrough

A suggested end-to-end tour of the platform (roughly 5–10 minutes):

1. **Login & RBAC** — sign in as a demo investigator with a defined clearance level.
2. **Investigation Workspace (`Overview`)** — review the active case summary, threat level, and headline metrics.
3. **Evidence Ingestion Hub** — inspect source records (FIR narrative, CDR bursts, bank transfers, geospatial traces) and their SHA-256 integrity hashes.
4. **11-Stage Pipeline** — run the full pipeline and watch each stage execute in sequence.
5. **Entity Explorer** — compare raw *mentioned* entities against *resolved* canonical entities.
6. **Resolution Workbench** — review a candidate identity match, inspect its similarity signals, and confirm the canonical link.
7. **Temporal Knowledge Graph** — center on a subject, expand their 1-hop/2-hop network, and trace hidden links between two entities.
8. **7 Crime Lenses** — switch the same graph between different crime-type views.
9. **Cross-Crime Radar** — identify entities that bridge multiple criminal activities.
10. **Explainable Leads** — open a generated lead and review its evidence-backed justification and citations.
11. **Human Review** — accept, reject, or escalate a lead with a recorded justification.
12. **Audit Trail** — view the immutable, hash-chained log of every action taken during the session.

## Repository Structure

```
.
├── backend/          # API server and core pipeline logic
├── netralink/         # Core application / library code
├── frontend/          # Investigative dashboard UI
├── dataset/           # Raw source datasets for the demo case
├── data/processed/    # Processed / derived data used by the graph
├── scripts/           # Utility and test scripts
├── run_app.py         # Single entry point: seeds data, starts API + UI
└── triggers.json      # Rule/trigger definitions used by the pipeline
```

*(See each folder for further detail; this is a high-level map, not an exhaustive file listing.)*

## Verification / Tests

An automated suite exercises the platform's user journeys end-to-end:

```bash
python scripts/test_enterprise_platform.py
```

## Ethics & Human-in-the-Loop

NetraLink is designed as a **decision-support** tool, not a decision-making one:

- The system generates *leads*, never verdicts — every lead requires explicit human review before being marked actionable.
- Every lead is explainable: each claim is traceable back to specific source evidence.
- Every investigator action is logged to an append-only, hash-verified audit trail.

## Disclaimer

This is a **prototype** built for a hackathon demonstration. The seeded "Operation Eclipse" case, all entities, names, and records are **entirely fictional** and used only to illustrate the platform's capabilities. This project is not deployed or certified for real investigative use.
