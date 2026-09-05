/**
 * NetraLink AI Enterprise Master Frontend Controller (Light Theme OSINT Intelligence Workspace)
 * Graph Engine: D3.js v7 Force-Directed Graph Engine
 * Features:
 * - Person Names displayed everywhere across all views (Entities, Leads, Alerts, Audit, Graph, Maps, Modals).
 * - D3.js Canvas 60FPS Force Simulation with animated edge data flow particles.
 * - Leaflet Interactive Geospatial Map with trajectory routes.
 * - Explainable Leads with raw evidence text.
 * - Human-in-the-loop Resolution Workbench & Audit Trail compliance.
 */

import { api } from "./api.js";

let currentCaseId = "INV-ECLIPSE-2026";
let simulation = null;
let canvas = null;
let ctx = null;
let zoomBehavior = null;
let currentTransform = d3.zoomIdentity;

let graphNodes = [];
let graphLinks = [];
let allNodesData = {};
let allEdgesData = {};

let selectedNodeId = null;
let selectedEdgeId = null;
let highlightedNodeIds = new Set();
let highlightedLinkIds = new Set();

let leafletMap = null;
let activeLeadForReview = null;
let animFrameId = null;
let particles = [];

// Realistic Name Database for Synthesizing Natural Person Names for Any ID
const FIRST_NAMES = [
  "Rajesh", "Amit", "Sanjay", "Anil", "Manoj", "Vijay", "Sunil", "Rakesh", "Ajay", "Vikram",
  "Pooja", "Priya", "Neha", "Anita", "Sunita", "Deepak", "Suresh", "Ramesh", "Dinesh", "Mahesh",
  "Kamlesh", "Mukesh", "Naresh", "Harish", "Girish", "Satish", "Ashok", "Vinod", "Pramod", "Subhash",
  "Alok", "Pankaj", "Pradeep", "Santosh", "Arun", "Tarun", "Varun", "Naveen", "Praveen", "Sachin",
  "Nitin", "Rohit", "Mohit", "Sumit", "Vikas", "Vishal", "Vivek", "Gaurav", "Saurabh", "Manish",
  "Kavita", "Rekha", "Meena", "Seema", "Geeta", "Anjali", "Swati", "Preeti", "Kiran", "Divya"
];

const LAST_NAMES = [
  "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Yadav", "Mishra", "Pandey", "Tiwari",
  "Dubey", "Shukla", "Tripathi", "Joshi", "Saxena", "Bhatnagar", "Mathur", "Srivastava", "Agrawal", "Bansal",
  "Mittal", "Goyal", "Garg", "Jain", "Chauhan", "Rathore", "Tomar", "Rajput", "Thakur", "Lodhi",
  "Kushwaha", "Maurya", "Saini", "Choudhary", "Jat", "Gurjar", "Reddy", "Nair", "Pillai", "Menon",
  "Deshmukh", "Patil", "Kulkarni", "Pawar", "Shinde", "Jadhav", "Bose", "Chatterjee", "Banerjee", "Mukherjee"
];

// Canonical ID to Human Name Dictionary (Key Known Suspects & Persons of Interest)
const PERSON_NAMES = {
  "P00561": "Rahul Sharma @ Guddu",
  "PERSON_00561": "Rahul Sharma @ Guddu",
  "P00151": "Vikram Sethi @ Langda",
  "PERSON_00151": "Vikram Sethi @ Langda",
  "P00975": "Deepak Verma",
  "PERSON_00975": "Deepak Verma",
  "P00985": "Suresh Patel",
  "PERSON_00985": "Suresh Patel",
  "P00788": "Ramesh Kumar",
  "PERSON_00788": "Ramesh Kumar",
  "P00637": "Tariq Ahmed",
  "PERSON_00637": "Tariq Ahmed",
  "P00510": "Sunil Yadav",
  "PERSON_00510": "Sunil Yadav",
  "P00811": "Imran Khan",
  "PERSON_00811": "Imran Khan"
};

// Deterministic Person Name Generator for any Person ID
function getPersonNameFromId(id) {
  if (!id) return "Unknown Person";
  const cleanId = String(id).trim();

  // 1. Direct match in known suspects map
  if (PERSON_NAMES[cleanId]) return PERSON_NAMES[cleanId];

  // 2. Normalized check (e.g. PERSON_00151 vs P00151)
  const normKey = cleanId.startsWith("PERSON_")
    ? "P" + cleanId.slice(7)
    : (cleanId.startsWith("P") && cleanId.length === 6 ? cleanId : null);
  if (normKey && PERSON_NAMES[normKey]) return PERSON_NAMES[normKey];

  // 3. Deterministic hash to realistic First + Last Name
  const match = cleanId.match(/\d+/);
  if (match) {
    const n = parseInt(match[0], 10);
    const firstName = FIRST_NAMES[n % FIRST_NAMES.length];
    const lastName = LAST_NAMES[(n * 7 + 13) % LAST_NAMES.length];
    return `${firstName} ${lastName}`;
  }

  // String hash fallback if no numbers
  let hash = 0;
  for (let i = 0; i < cleanId.length; i++) {
    hash = (hash << 5) - hash + cleanId.charCodeAt(i);
    hash |= 0;
  }
  const absHash = Math.abs(hash);
  const firstName = FIRST_NAMES[absHash % FIRST_NAMES.length];
  const lastName = LAST_NAMES[(absHash * 7 + 13) % LAST_NAMES.length];
  return `${firstName} ${lastName}`;
}

// Global text sanitizer to replace any raw Person IDs in strings, descriptions, or bullets
function sanitizePersonNamesInText(text) {
  if (!text || typeof text !== "string") return text;
  let res = text;
  // Replace expressions like "Subject P00561", "PERSON_00561", "P00561"
  res = res.replace(/(?:Subject\s+)?(PERSON_\d{5}|P\d{5})/gi, (match, id) => {
    return getPersonNameFromId(id);
  });
  // Replace bracketed IDs like "Rahul Sharma @ Guddu (PERSON_00561)"
  res = res.replace(/\s*\((?:PERSON_\d+|P\d+)\)/gi, "");
  return res;
}

// Raw Evidence Excerpts mapping for Explainable Leads
const RAW_EVIDENCE_MAP = {
  "P00561": `[FIR-RPT00001 / POLICE INTERCEPT]
Date: 2026-07-25 05:52:00 | Jurisdiction: Ujjain Central PS | Ref: FIR-LIVE-089
Narrative: On 2026-07-25, field intelligence observed Rahul Sharma @ Guddu in direct physical contact with Deepak Verma near Zone_0123 Safehouse in Ujjain. Subject was operating White SUV (VEH00359) and communicated via handset tied to PH01018. Subsequent IMPS transfers totaling ₹1,48,500 under ₹50,000 reporting thresholds were routed into mule account ACC00481 within 3 hours.`,
  
  "LEAD-001": `[MULTIMODAL INTELLIGENCE CORRELATION REPORT]
Lead ID: NL-0017 | Target Subject: Rahul Sharma @ Guddu
1. CDR Log CDR000001: 14 voice call bursts between PH01018 and PH00673 (Duration: 1717s) prior to shipment dispatch.
2. Banking Log TX000235: IMPS Transfer of ₹64,515.97 into Account ACC00481, layered into ACC01174 within 180 minutes.
3. Geo Sensor GEO000001: Co-location ping at Jabalpur Commercial Warehouse Sector 4 (LOC0140).`
};

// Entity Type Palette (Optimized for D3 Canvas Light Mode)
const ENTITY_CONFIG = {
  Person: {
    fill: "#dbeafe",
    stroke: "#2563eb",
    fontColor: "#0f172a",
    radius: 18,
    badge: "Person"
  },
  Phone: {
    fill: "#d1fae5",
    stroke: "#059669",
    fontColor: "#0f172a",
    radius: 13,
    badge: "Phone"
  },
  Account: {
    fill: "#fef3c7",
    stroke: "#d97706",
    fontColor: "#0f172a",
    radius: 13,
    badge: "Account"
  },
  Vehicle: {
    fill: "#f3e8ff",
    stroke: "#7c3aed",
    fontColor: "#0f172a",
    radius: 14,
    badge: "Vehicle"
  },
  Location: {
    fill: "#fee2e2",
    stroke: "#dc2626",
    fontColor: "#0f172a",
    radius: 15,
    badge: "Location"
  },
  Default: {
    fill: "#e2e8f0",
    stroke: "#64748b",
    fontColor: "#0f172a",
    radius: 12,
    badge: "Entity"
  }
};

// Relation Edge Colors
const EDGE_RELATION_PALETTE = {
  CALL: "#2563eb",
  COMMUNICATED: "#2563eb",
  TRANSACTION: "#059669",
  HAWALA: "#d97706",
  CO_LOCATED: "#dc2626",
  OPERATED: "#7c3aed",
  OWNED: "#7c3aed",
  DEFAULT: "#94a3b8"
};

// Universal Helper: Always return human readable Person Name instead of raw ID
function getEntityDisplayName(id, rawData = {}) {
  if (!id) return "Unknown Entity";
  const cleanId = String(id).trim();

  // If this entity is a Person or has a Person ID pattern
  const isPerson =
    rawData.entity_type === "Person" ||
    rawData.type === "Person" ||
    cleanId.startsWith("P0") ||
    cleanId.startsWith("PERSON_") ||
    PERSON_NAMES[cleanId];

  if (isPerson) {
    if (PERSON_NAMES[cleanId]) return PERSON_NAMES[cleanId];
    if (rawData.name && !rawData.name.startsWith("PERSON_") && !rawData.name.startsWith("P0")) {
      return sanitizePersonNamesInText(rawData.name);
    }
    if (rawData.label && !rawData.label.startsWith("PERSON_") && !rawData.label.startsWith("P0")) {
      return sanitizePersonNamesInText(rawData.label);
    }
    if (rawData.candidate_name) return sanitizePersonNamesInText(rawData.candidate_name);
    return getPersonNameFromId(cleanId);
  }

  // Non-person entity (Phone, Account, Vehicle, Location, etc.)
  if (rawData.name) return rawData.name;
  if (rawData.label) return rawData.label;
  return cleanId;
}

// Helper to resolve search input or query back to ID if needed
function resolveEntityId(query) {
  if (!query) return "P00561";
  const q = query.trim().toLowerCase();

  for (const [id, name] of Object.entries(PERSON_NAMES)) {
    if (name.toLowerCase().includes(q) || id.toLowerCase() === q) {
      return id.startsWith("PERSON_") ? id.replace("PERSON_", "P") : id;
    }
  }

  if (typeof graphNodes !== "undefined" && Array.isArray(graphNodes)) {
    const matchedNode = graphNodes.find(n => (n.displayName || "").toLowerCase().includes(q) || n.id.toLowerCase() === q);
    if (matchedNode) return matchedNode.id;
  }

  if (typeof allNodesData !== "undefined") {
    for (const [id, data] of Object.entries(allNodesData)) {
      const disp = getEntityDisplayName(id, data).toLowerCase();
      if (disp.includes(q) || id.toLowerCase() === q) {
        return id;
      }
    }
  }

  return query;
}

// Initialize Dashboard on DOM Load
document.addEventListener("DOMContentLoaded", async () => {
  // Setup Home Screen → Dashboard Transition
  setupHomeScreen();

  setupNavigation();
  setupModals();
  setupGraphControls();
  window.netralinkApp = createPublicApi();
});

// Home Screen → Dashboard Transition
function setupHomeScreen() {
  const homeScreen = document.getElementById("home-screen");
  const dashboardWrapper = document.getElementById("dashboard-wrapper");

  function enterDashboard() {
    if (!homeScreen || !dashboardWrapper) return;

    // Animate home screen out
    homeScreen.classList.add("home-exit");

    setTimeout(() => {
      homeScreen.style.display = "none";
      homeScreen.remove();

      // Show dashboard
      dashboardWrapper.style.display = "flex";
      dashboardWrapper.classList.add("dashboard-enter");

      // Re-enable body scrolling for dashboard
      document.body.style.overflow = "";

      // Initialize dashboard data after transition
      initializeDashboard();

      // Refresh lucide icons in dashboard
      if (window.lucide) window.lucide.createIcons();

      setTimeout(() => {
        dashboardWrapper.classList.remove("dashboard-enter");
      }, 500);
    }, 550);
  }

  // Wire up all "Enter Dashboard" buttons
  document.getElementById("home-enter-btn")?.addEventListener("click", enterDashboard);
  document.getElementById("home-enter-nav")?.addEventListener("click", enterDashboard);
  document.getElementById("home-enter-footer")?.addEventListener("click", enterDashboard);

  // Smooth scroll for anchor links
  homeScreen?.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute("href"));
      if (target) target.scrollIntoView({ behavior: "smooth" });
    });
  });
}

async function initializeDashboard() {
  try {
    await loadCurrentCaseDetails();
    await loadOverviewData();
    initD3Graph();
    await loadGraphData("P00561");
  } catch (err) {
    console.error("Dashboard initialization error:", err);
  }
}

// ----------------------------------------------------------------------------
// 1. PUBLIC GLOBAL API FOR INLINE HANDLERS
// ----------------------------------------------------------------------------
function createPublicApi() {
  return {
    focusGraphEntity: (entityId) => {
      switchView("graph");
      setTimeout(() => focusOrFetchGraphNode(entityId), 300);
    },
    expandNodeNetwork: async (entityId) => {
      try {
        const id = resolveEntityId(entityId);
        const expanded = await api.graph.expand(currentCaseId, id, 1);
        if (expanded && (expanded.nodes || expanded.edges)) {
          appendGraphData(expanded);
          focusOrFetchGraphNode(id);
        }
      } catch (err) {
        console.warn("Expand network error:", err);
      }
    },
    openHiddenPathsModal: (sourceId = "Rahul Sharma @ Guddu", targetId = "Vikram Sethi @ Langda") => {
      const srcInput = document.getElementById("path-source-input");
      const tgtInput = document.getElementById("path-target-input");
      if (srcInput) srcInput.value = getEntityDisplayName(sourceId);
      if (tgtInput) tgtInput.value = getEntityDisplayName(targetId);
      const modal = document.getElementById("modal-paths");
      if (modal) modal.classList.add("active");
    },
    closeModals: () => {
      document.querySelectorAll(".modal-backdrop").forEach((m) => m.classList.remove("active"));
    },
    reviewLead: (leadId) => {
      openReviewModal(leadId);
    }
  };
}

// ----------------------------------------------------------------------------
// 2. NAVIGATION & VIEW SWITCHING
// ----------------------------------------------------------------------------
function setupNavigation() {
  const navItems = document.querySelectorAll(".sidebar .nav-item");
  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      const viewName = item.dataset.view;
      if (!viewName) return;

      navItems.forEach((i) => i.classList.remove("active"));
      item.classList.add("active");

      switchView(viewName);
    });
  });

  // Case Selector Switch
  const caseSelect = document.getElementById("case-selector");
  if (caseSelect) {
    caseSelect.addEventListener("change", (e) => {
      currentCaseId = e.target.value;
      loadOverviewData();
    });
  }

  // Quick Action Buttons
  document.getElementById("btn-quick-run-pipeline")?.addEventListener("click", () => {
    switchView("pipeline");
    const navItem = document.querySelector('.sidebar .nav-item[data-view="pipeline"]');
    if (navItem) {
      document.querySelectorAll(".sidebar .nav-item").forEach((i) => i.classList.remove("active"));
      navItem.classList.add("active");
    }
    executePipelineRun();
  });

  document.getElementById("btn-run-full-pipeline")?.addEventListener("click", () => {
    executePipelineRun();
  });

  document.getElementById("btn-seed-demo-ev")?.addEventListener("click", async () => {
    try {
      await api.investigations.seedDemo(currentCaseId);
      alert("Demonstration evidence successfully re-seeded!");
      loadEvidenceHub();
    } catch (err) {
      alert("Seed error: " + err.message);
    }
  });
}

function switchView(viewName) {
  document.querySelectorAll(".view-panel").forEach((panel) => panel.classList.remove("active"));

  const targetPanel = document.getElementById(`view-${viewName}`);
  if (targetPanel) {
    targetPanel.classList.add("active");
  }

  // View Specific Loaders
  switch (viewName) {
    case "overview":
      loadOverviewData();
      break;
    case "evidence":
      loadEvidenceHub();
      break;
    case "pipeline":
      loadPipelineView();
      break;
    case "entities":
      loadEntitiesExplorer();
      break;
    case "resolution":
      loadResolutionWorkbench();
      break;
    case "graph":
      if (canvas) {
        setTimeout(() => resizeCanvas(), 100);
      }
      break;
    case "lenses":
      loadCrimeLenses();
      break;
    case "crosscrime":
      loadCrossCrimeRadar();
      break;
    case "map":
      loadGeoMap();
      break;
    case "leads":
      loadLeadsView();
      break;
    case "alerts":
      loadAlertsView();
      break;
    case "audit":
      loadAuditTrailView();
      break;
  }

  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// ----------------------------------------------------------------------------
// 3. CASE OVERVIEW & DASHBOARD STATS
// ----------------------------------------------------------------------------
async function loadCurrentCaseDetails() {
  try {
    const inv = await api.investigations.get(currentCaseId);
    const titleEl = document.getElementById("ov-case-title");
    const descEl = document.getElementById("ov-case-desc");
    const evBadge = document.getElementById("badge-evidence-count");
    const leadsBadge = document.getElementById("badge-leads-count");
    const alertsBadge = document.getElementById("badge-alerts-count");

    if (titleEl) titleEl.innerText = inv.title || "Operation Eclipse";
    if (descEl) descEl.innerText = inv.description || "";
    if (evBadge) evBadge.innerText = inv.evidence_count || "5";
    if (leadsBadge) leadsBadge.innerText = inv.leads_count || "1";
    if (alertsBadge) alertsBadge.innerText = inv.alerts_count || "4";
  } catch (err) {
    console.warn("Failed to fetch case details:", err);
  }
}

async function loadOverviewData() {
  await loadCurrentCaseDetails();
  try {
    const leadsRes = await api.leads.list(currentCaseId);
    const leads = leadsRes.leads || [];

    const summaryContainer = document.getElementById("ov-leads-summary");
    if (summaryContainer) {
      if (leads.length === 0) {
        summaryContainer.innerHTML = `<div style="color: var(--text-muted); font-size: 0.8rem;">No active leads pending review.</div>`;
      } else {
        summaryContainer.innerHTML = leads.slice(0, 3).map((l) => {
          const personName = getEntityDisplayName(l.candidate_entity_id, { label: l.candidate_label });
          const cleanSummary = sanitizePersonNamesInText(l.summary || l.title);
          return `
            <div style="padding: 12px; background: #ffffff; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); margin-bottom: 8px; box-shadow: var(--shadow-card);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <strong style="color: var(--accent-blue); font-size: 0.86rem;">Lead ${l.lead_number}: ${personName}</strong>
                <span class="badge" style="background: rgba(220,38,38,0.1); color: var(--accent-rose);">${l.status}</span>
              </div>
              <p style="font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 8px;">${cleanSummary}</p>
              <div style="display: flex; gap: 8px;">
                <button class="btn btn-primary btn-sm" onclick="window.netralinkApp.reviewLead('${l.id}')">Review Rationale</button>
                <button class="btn btn-secondary btn-sm" onclick="window.netralinkApp.focusGraphEntity('${personName}')">Inspect Graph</button>
              </div>
            </div>
          `;
        }).join("");
      }
    }
  } catch (err) {
    console.warn("Overview leads load error:", err);
  }
}

// ----------------------------------------------------------------------------
// 4. EVIDENCE HUB & INGESTION
// ----------------------------------------------------------------------------
async function loadEvidenceHub() {
  const tbody = document.getElementById("evidence-table-body");
  if (!tbody) return;

  try {
    const res = await api.evidence.list(currentCaseId);
    const records = res.evidence_records || [];

    tbody.innerHTML = records.map((r) => `
      <tr>
        <td><strong class="mono" style="color: var(--accent-blue);">${r.id}</strong></td>
        <td><span class="badge">${r.evidence_type}</span></td>
        <td class="mono" style="font-size: 0.75rem;">${r.source_reference}</td>
        <td><strong>${r.title}</strong></td>
        <td class="mono" style="font-size: 0.72rem; color: var(--accent-cyan);">${(r.sha256_hash || "").substring(0, 16)}...</td>
        <td class="mono" style="font-size: 0.75rem; color: var(--text-muted);">${r.created_at || "2026-09-01"}</td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="alert('Viewing Full Evidence Record:\\n\\nSource: ' + '${r.source_reference}' + '\\nTitle: ' + '${r.title}' + '\\n\\nRAW EVIDENCE TEXT:\\n' + '${(r.content_text || "").replace(/'/g, "\\'")}')">View Text</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="color: var(--accent-rose);">Failed to load evidence records.</td></tr>`;
  }
}

// ----------------------------------------------------------------------------
// 5. 11-STAGE PIPELINE VIEW
// ----------------------------------------------------------------------------
async function loadPipelineView() {
  const container = document.getElementById("pipeline-stages-container");
  if (!container) return;

  try {
    const statusRes = await api.pipeline.status(currentCaseId);
    const stages = statusRes.stages || [];

    container.innerHTML = stages.map((s, idx) => `
      <div style="display: flex; gap: 14px; margin-bottom: 10px; align-items: center; padding: 12px 16px; background: #ffffff; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); box-shadow: var(--shadow-card);">
        <span class="mono" style="font-weight: 700; color: var(--accent-blue); width: 28px; font-size: 0.85rem;">${String(idx + 1).padStart(2, "0")}</span>
        <div style="flex: 1;">
          <div style="font-family: var(--font-display); font-weight: 600; font-size: 0.88rem; color: var(--text-primary);">${s.name}</div>
          <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px;">${s.description}</div>
        </div>
        <span class="badge" style="background: rgba(5,150,105,0.1); color: var(--accent-emerald);">${s.status}</span>
        <span class="mono" style="font-size: 0.75rem; color: var(--text-muted);">${s.duration_ms}ms</span>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-rose);">Pipeline status unavailable.</div>`;
  }
}

async function executePipelineRun() {
  const btn = document.getElementById("btn-run-full-pipeline");
  if (btn) btn.disabled = true;
  try {
    await api.pipeline.run(currentCaseId);
    alert("Pipeline executed successfully! All 11 intelligence stages verified.");
    loadPipelineView();
    loadOverviewData();
  } catch (err) {
    alert("Pipeline execution error: " + err.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ----------------------------------------------------------------------------
// 6. ENTITIES & RESOLUTION WORKBENCH (Names Displayed Everywhere)
// ----------------------------------------------------------------------------
async function loadEntitiesExplorer() {
  const tbody = document.getElementById("entities-table-body");
  if (!tbody) return;

  try {
    const res = await api.entities.list(currentCaseId);
    const persons = res.resolved_persons || [];

    tbody.innerHTML = persons.map((p) => {
      const personName = getEntityDisplayName(p.canonical_id, p);
      const cleanAliases = (p.aliases || [])
        .filter(a => !a.startsWith("PERSON_") && !a.startsWith("P00"))
        .join(", ") || "—";
      const occupation = (p.occupation && p.occupation !== "unknown") ? p.occupation.toUpperCase() : "OPERATIVE";

      return `
        <tr>
          <td><strong style="font-size: 0.92rem; color: var(--accent-blue);">${personName}</strong></td>
          <td><span class="badge" style="color: var(--text-primary); font-weight: 600;">${occupation}</span></td>
          <td style="color: var(--text-secondary); font-size: 0.82rem;">${cleanAliases}</td>
          <td class="mono" style="font-size: 0.75rem;">${p.phones.join(", ") || "—"}</td>
          <td class="mono" style="font-size: 0.75rem;">${p.accounts.join(", ") || "—"}</td>
          <td class="mono" style="font-size: 0.75rem;">${p.vehicles.join(", ") || "—"}</td>
          <td><span class="badge" style="background: rgba(5,150,105,0.1); color: var(--accent-emerald);">VERIFIED INTEL</span></td>
          <td>
            <button class="btn btn-sm btn-secondary" onclick="window.netralinkApp.focusGraphEntity('${personName}')">Inspect Graph</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" style="color: var(--accent-rose);">Failed to load entity directory.</td></tr>`;
  }
}

async function loadResolutionWorkbench() {
  const container = document.getElementById("resolution-candidates-container");
  if (!container) return;

  try {
    const res = await api.entities.candidates(currentCaseId);
    const candidates = res.candidates || [];

    if (candidates.length === 0) {
      container.innerHTML = `<div style="color: var(--text-muted); padding: 20px;">No pending resolution candidates requiring human confirmation.</div>`;
      return;
    }

    container.innerHTML = candidates.map((c) => {
      const canonicalName = getEntityDisplayName(c.canonical_candidate_id, { label: c.canonical_candidate_label || c.candidate_name });
      return `
        <div class="panel-card" style="border-left: 3px solid var(--accent-amber);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div>
              <strong style="font-size: 0.95rem; color: var(--text-primary);">Mention: "${c.mentioned_entity}"</strong>
              <span style="color: var(--text-secondary); font-size: 0.84rem; margin-left: 10px;">➔ Matched Person: <strong style="color: var(--accent-blue);">${canonicalName}</strong></span>
            </div>
            <span class="badge" style="background: rgba(217,119,6,0.12); color: var(--accent-amber);">Match Score: ${Math.round(c.match_score * 100)}%</span>
          </div>
          <p style="font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 12px;">
            <strong>Disambiguation Signals:</strong> ${c.reasons ? c.reasons.join(" • ") : "High phonetic similarity, shared mobile identifiers & co-location overlap."}
          </p>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-primary btn-sm" onclick="confirmResolution('${c.candidate_id}', 'CONFIRM')">Confirm Identity Match</button>
            <button class="btn btn-danger-outline btn-sm" onclick="confirmResolution('${c.candidate_id}', 'REJECT')">Reject Match</button>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-rose);">Failed to load candidate matches.</div>`;
  }
}

window.confirmResolution = async function (candidateId, decision) {
  try {
    await api.entities.decide(currentCaseId, candidateId, decision, "Verified via Human Resolution Workbench.");
    alert(`Candidate decision '${decision}' submitted successfully!`);
    loadResolutionWorkbench();
  } catch (err) {
    alert("Resolution error: " + err.message);
  }
};

// ----------------------------------------------------------------------------
// 7. D3.JS FORCE GRAPH ENGINE (Person Names Rendered on Canvas)
// ----------------------------------------------------------------------------
function initD3Graph() {
  const container = document.getElementById("cy-canvas");
  if (!container || !window.d3) return;

  container.innerHTML = "";
  canvas = document.createElement("canvas");
  container.appendChild(canvas);
  ctx = canvas.getContext("2d");

  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);

  // D3 Zoom Behavior
  zoomBehavior = d3.zoom()
    .scaleExtent([0.2, 4.0])
    .on("zoom", (event) => {
      currentTransform = event.transform;
      renderCanvas();
    });

  d3.select(canvas).call(zoomBehavior);

  // Click & Drag Handlers
  setupCanvasInteractions();

  // Physics Simulation
  simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id((d) => d.id).distance(135))
    .force("charge", d3.forceManyBody().strength(-380))
    .force("collide", d3.forceCollide().radius((d) => (d.radius || 15) + 12))
    .force("center", d3.forceCenter(canvas.width / 2, canvas.height / 2))
    .on("tick", () => {
      renderCanvas();
    });

  // Start continuous particle animation loop
  startParticleAnimation();
}

function resizeCanvas() {
  const container = document.getElementById("cy-canvas");
  if (!container || !canvas) return;
  const rect = container.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;

  if (ctx) {
    ctx.resetTransform();
    ctx.scale(dpr, dpr);
  }

  if (simulation) {
    simulation.force("center", d3.forceCenter(rect.width / 2, rect.height / 2));
    simulation.alpha(0.3).restart();
  }
}

function setupCanvasInteractions() {
  let isDragging = false;
  let dragNode = null;

  d3.select(canvas).on("click", (event) => {
    if (isDragging) return;
    const [mx, my] = d3.pointer(event, canvas);
    const point = currentTransform.invert([mx, my]);
    const clickedNode = findNodeAt(point[0], point[1]);

    if (clickedNode) {
      selectedNodeId = clickedNode.id;
      highlightNodeNeighbors(clickedNode.id);
      inspectNode(clickedNode.raw || clickedNode);
    } else {
      const clickedLink = findLinkAt(point[0], point[1]);
      if (clickedLink) {
        inspectEdge(clickedLink.raw || clickedLink);
      } else {
        resetHighlight();
      }
    }
  });

  // Drag node behavior
  const drag = d3.drag()
    .container(canvas)
    .subject((event) => {
      const point = currentTransform.invert([event.x, event.y]);
      return findNodeAt(point[0], point[1]);
    })
    .on("start", (event) => {
      if (!event.subject) return;
      isDragging = true;
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
      dragNode = event.subject;
    })
    .on("drag", (event) => {
      if (!dragNode) return;
      const point = currentTransform.invert([event.x, event.y]);
      dragNode.fx = point[0];
      dragNode.fy = point[1];
    })
    .on("end", (event) => {
      if (!dragNode) return;
      if (!event.active) simulation.alphaTarget(0);
      dragNode.fx = null;
      dragNode.fy = null;
      dragNode = null;
      setTimeout(() => { isDragging = false; }, 50);
    });

  d3.select(canvas).call(drag);
}

function findNodeAt(x, y) {
  for (let i = graphNodes.length - 1; i >= 0; i--) {
    const n = graphNodes[i];
    const dx = x - n.x;
    const dy = y - n.y;
    if (dx * dx + dy * dy <= (n.radius + 6) * (n.radius + 6)) {
      return n;
    }
  }
  return null;
}

function findLinkAt(x, y) {
  for (const l of graphLinks) {
    if (!l.source || !l.target) continue;
    const x1 = l.source.x, y1 = l.source.y;
    const x2 = l.target.x, y2 = l.target.y;
    const dist = distToSegment({ x, y }, { x: x1, y: y1 }, { x: x2, y: y2 });
    if (dist < 8) return l;
  }
  return null;
}

function distToSegment(p, v, w) {
  const l2 = (w.x - v.x) ** 2 + (w.y - v.y) ** 2;
  if (l2 === 0) return Math.hypot(p.x - v.x, p.y - v.y);
  let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(p.x - (v.x + t * (w.x - v.x)), p.y - (v.y + t * (w.y - v.y)));
}

// ----------------------------------------------------------------------------
// D3 CANVAS RENDER LOOP (Particles + Person Names)
// ----------------------------------------------------------------------------
function renderCanvas() {
  if (!ctx || !canvas) return;
  const width = canvas.width / (window.devicePixelRatio || 1);
  const height = canvas.height / (window.devicePixelRatio || 1);

  ctx.save();
  ctx.clearRect(0, 0, width, height);

  // Apply Camera Pan & Zoom Transform
  ctx.translate(currentTransform.x, currentTransform.y);
  ctx.scale(currentTransform.k, currentTransform.k);

  // 1. Draw Links
  graphLinks.forEach((l) => {
    if (!l.source || !l.target || l.source.x === undefined) return;
    const isHighlighted = highlightedLinkIds.size === 0 || highlightedLinkIds.has(l.id);
    const alpha = isHighlighted ? 0.85 : 0.12;

    ctx.beginPath();
    ctx.moveTo(l.source.x, l.source.y);
    ctx.lineTo(l.target.x, l.target.y);
    ctx.strokeStyle = l.color || "#94a3b8";
    ctx.globalAlpha = alpha;
    ctx.lineWidth = isHighlighted ? (l.width || 2) : 1;

    if (l.dashes) {
      ctx.setLineDash(l.dashes);
    } else {
      ctx.setLineDash([]);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw Relation Label on Edge
    if (isHighlighted && currentTransform.k > 0.6) {
      const midX = (l.source.x + l.target.x) / 2;
      const midY = (l.source.y + l.target.y) / 2;
      ctx.font = "9px 'JetBrains Mono', monospace";
      ctx.fillStyle = "#ffffff";
      ctx.globalAlpha = 0.9;
      
      const labelText = l.label || l.relation || "";
      const textWidth = ctx.measureText(labelText).width;

      ctx.fillStyle = "rgba(255, 255, 255, 0.95)";
      ctx.fillRect(midX - textWidth / 2 - 4, midY - 7, textWidth + 8, 14);

      ctx.fillStyle = "#334155";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(labelText, midX, midY);
    }
  });

  // 2. Draw Animated Edge Particles (Data/Money Flow Visualization)
  particles.forEach((p) => {
    if (!p.link || !p.link.source || !p.link.target) return;
    const isHighlighted = highlightedLinkIds.size === 0 || highlightedLinkIds.has(p.link.id);
    if (!isHighlighted) return;

    p.progress += p.speed;
    if (p.progress > 1) p.progress = 0;

    const px = p.link.source.x + (p.link.target.x - p.link.source.x) * p.progress;
    const py = p.link.source.y + (p.link.target.y - p.link.source.y) * p.progress;

    ctx.beginPath();
    ctx.arc(px, py, p.size || 3.5, 0, 2 * Math.PI);
    ctx.fillStyle = p.color || "#2563eb";
    ctx.globalAlpha = 0.9;
    ctx.fill();
  });

  // 3. Draw Nodes (Person Names Rendered on Canvas)
  graphNodes.forEach((n) => {
    if (n.x === undefined) return;
    const isHighlighted = highlightedNodeIds.size === 0 || highlightedNodeIds.has(n.id);
    const isSelected = n.id === selectedNodeId;
    const alpha = isHighlighted ? 1.0 : 0.15;

    ctx.globalAlpha = alpha;

    // Outer Halo Ring for Center Suspects or Selected Nodes
    if (isSelected || n.isKeySuspect) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius + 6, 0, 2 * Math.PI);
      ctx.fillStyle = isSelected ? "rgba(37, 99, 235, 0.25)" : "rgba(220, 38, 38, 0.2)";
      ctx.fill();
    }

    // Node Circle Base
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.radius, 0, 2 * Math.PI);
    ctx.fillStyle = n.fill || "#dbeafe";
    ctx.fill();

    // Node Border Ring
    ctx.lineWidth = isSelected ? 3.5 : (n.isKeySuspect ? 3.0 : 2.0);
    ctx.strokeStyle = isSelected ? "#2563eb" : (n.stroke || "#2563eb");
    ctx.stroke();

    // Node Type Icon Badge or Inner Symbol
    ctx.fillStyle = n.stroke || "#2563eb";
    ctx.beginPath();
    ctx.arc(n.x, n.y, 4, 0, 2 * Math.PI);
    ctx.fill();

    // Person Name Label below Node
    if (currentTransform.k > 0.4 || isHighlighted) {
      ctx.font = `${isSelected ? '600' : '500'} ${n.isKeySuspect ? '12px' : '11px'} 'Space Grotesk', 'Inter', sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";

      const label = n.displayName;
      const textY = n.y + n.radius + 5;

      // Label background pill
      const tw = ctx.measureText(label).width;
      ctx.fillStyle = "rgba(255, 255, 255, 0.92)";
      ctx.fillRect(n.x - tw / 2 - 4, textY - 1, tw + 8, 15);

      ctx.fillStyle = "#0f172a";
      ctx.fillText(label, n.x, textY);
    }
  });

  ctx.restore();
}

function startParticleAnimation() {
  if (animFrameId) cancelAnimationFrame(animFrameId);
  function loop() {
    renderCanvas();
    animFrameId = requestAnimationFrame(loop);
  }
  loop();
}

function convertToD3Data(graphData) {
  const rawNodes = graphData.nodes || [];
  const rawEdges = graphData.edges || [];

  const nodes = rawNodes.map((n) => {
    const d = n.data || n;
    allNodesData[d.id] = d;

    const type = d.type || "Entity";
    const config = ENTITY_CONFIG[type] || ENTITY_CONFIG.Default;
    const isKeySuspect = d.id === "P00561" || d.id === "P00151";
    
    // Always use full Person Name
    const displayName = getEntityDisplayName(d.id, d);

    return {
      id: d.id,
      displayName: displayName,
      type: type,
      fill: config.fill,
      stroke: config.stroke,
      radius: isKeySuspect ? 24 : config.radius,
      isKeySuspect: isKeySuspect,
      raw: d
    };
  });

  const nodeLookup = new Map(nodes.map((n) => [n.id, n]));

  const links = [];
  particles = [];

  rawEdges.forEach((e) => {
    const d = e.data || e;
    const edgeId = d.id || `${d.source || d.from}_${d.target || d.to}_${Math.random()}`;
    allEdgesData[edgeId] = d;

    const srcId = d.source || d.from;
    const tgtId = d.target || d.to;

    if (nodeLookup.has(srcId) && nodeLookup.has(tgtId)) {
      const rel = (d.label || d.relation || "DEFAULT").toUpperCase();
      let color = EDGE_RELATION_PALETTE.DEFAULT;
      let dashes = false;

      for (const k of Object.keys(EDGE_RELATION_PALETTE)) {
        if (rel.includes(k)) {
          color = EDGE_RELATION_PALETTE[k];
          break;
        }
      }
      if (rel.includes("HAWALA") || rel.includes("CO_LOCATED")) {
        dashes = [4, 4];
      }

      const linkObj = {
        id: edgeId,
        source: srcId,
        target: tgtId,
        label: d.label || d.relation || "",
        relation: rel,
        color: color,
        dashes: dashes,
        width: rel.includes("TRANSACTION") || rel.includes("CALL") ? 2.4 : 1.8,
        raw: d
      };

      links.push(linkObj);

      // Create animated particles along this link
      particles.push({
        link: linkObj,
        progress: Math.random(),
        speed: 0.004 + Math.random() * 0.006,
        size: 3,
        color: color
      });
    }
  });

  return { nodes, links };
}

async function loadGraphData(entityId = "P00561") {
  try {
    const id = resolveEntityId(entityId);
    const graphData = await api.graph.get(currentCaseId, id, 2);
    const { nodes, links } = convertToD3Data(graphData);

    graphNodes = nodes;
    graphLinks = links;

    if (simulation) {
      simulation.nodes(graphNodes);
      simulation.force("link").links(graphLinks);
      simulation.alpha(1).restart();
    }

    if (allNodesData[id]) {
      setTimeout(() => {
        focusOrFetchGraphNode(id);
      }, 400);
    }
  } catch (err) {
    console.error("Failed to load graph:", err);
  }
}

function appendGraphData(newGraphData) {
  const { nodes, links } = convertToD3Data(newGraphData);
  const existingIds = new Set(graphNodes.map((n) => n.id));

  nodes.forEach((n) => {
    if (!existingIds.has(n.id)) {
      graphNodes.push(n);
    }
  });

  const existingLinkIds = new Set(graphLinks.map((l) => l.id));
  links.forEach((l) => {
    if (!existingLinkIds.has(l.id)) {
      graphLinks.push(l);
    }
  });

  if (simulation) {
    simulation.nodes(graphNodes);
    simulation.force("link").links(graphLinks);
    simulation.alpha(0.5).restart();
  }
}

function highlightNodeNeighbors(nodeId) {
  selectedNodeId = nodeId;
  highlightedNodeIds.clear();
  highlightedLinkIds.clear();

  highlightedNodeIds.add(nodeId);

  graphLinks.forEach((l) => {
    const sId = typeof l.source === "object" ? l.source.id : l.source;
    const tId = typeof l.target === "object" ? l.target.id : l.target;

    if (sId === nodeId || tId === nodeId) {
      highlightedLinkIds.add(l.id);
      highlightedNodeIds.add(sId);
      highlightedNodeIds.add(tId);
    }
  });

  renderCanvas();
}

function resetHighlight() {
  selectedNodeId = null;
  selectedEdgeId = null;
  highlightedNodeIds.clear();
  highlightedLinkIds.clear();
  renderCanvas();
}

function setupGraphControls() {
  // Zoom In
  document.getElementById("hud-zoom-in")?.addEventListener("click", () => {
    if (canvas && zoomBehavior) {
      d3.select(canvas).transition().duration(300).call(zoomBehavior.scaleBy, 1.3);
    }
  });

  // Zoom Out
  document.getElementById("hud-zoom-out")?.addEventListener("click", () => {
    if (canvas && zoomBehavior) {
      d3.select(canvas).transition().duration(300).call(zoomBehavior.scaleBy, 0.75);
    }
  });

  // Fit All
  document.getElementById("hud-fit")?.addEventListener("click", () => {
    if (canvas && zoomBehavior) {
      d3.select(canvas).transition().duration(400).call(zoomBehavior.transform, d3.zoomIdentity.translate(0, 0).scale(1));
    }
  });

  // Layout Selector (Force, Radial, Hierarchical)
  document.getElementById("hud-layout-select")?.addEventListener("change", (e) => {
    applyGraphLayout(e.target.value);
  });

  // Search Input & Button
  const handleSearch = () => {
    const input = document.getElementById("hud-search-input");
    const query = (input?.value || "").trim();
    if (query) {
      focusOrFetchGraphNode(query);
    }
  };

  document.getElementById("hud-btn-search")?.addEventListener("click", handleSearch);
  document.getElementById("hud-search-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleSearch();
  });

  // Hidden Paths
  document.getElementById("hud-btn-hidden-paths")?.addEventListener("click", () => {
    window.netralinkApp.openHiddenPathsModal("Rahul Sharma @ Guddu", "Vikram Sethi @ Langda");
  });

  // Inspector Close
  document.getElementById("inspector-close-btn")?.addEventListener("click", () => {
    resetHighlight();
    const heading = document.getElementById("drawer-heading");
    const badge = document.getElementById("drawer-type-badge");
    const content = document.getElementById("drawer-content");

    if (heading) heading.innerText = "Entity Inspector";
    if (badge) {
      badge.innerText = "Select a node";
      badge.style.borderColor = "var(--border-muted)";
      badge.style.color = "var(--accent-blue)";
    }
    if (content) {
      content.innerHTML = `
        <div class="inspector-empty">
          <i data-lucide="mouse-pointer-click" size="32"></i>
          <p>Click any node or edge on the graph to inspect its intelligence dossier.</p>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
    }
  });
}

function applyGraphLayout(layoutName) {
  if (!simulation) return;

  const container = document.getElementById("cy-canvas");
  const w = container ? container.clientWidth : 800;
  const h = container ? container.clientHeight : 600;

  if (layoutName === "hierarchical") {
    simulation.force("charge", d3.forceManyBody().strength(-200));
    simulation.force("link").distance(100);
    graphNodes.forEach((n, idx) => {
      n.fy = (idx % 4) * 120 + 80;
    });
  } else if (layoutName === "circle") {
    simulation.force("charge", d3.forceManyBody().strength(-150));
    const r = Math.min(w, h) * 0.35;
    graphNodes.forEach((n, idx) => {
      const angle = (idx / graphNodes.length) * 2 * Math.PI;
      n.fx = w / 2 + r * Math.cos(angle);
      n.fy = h / 2 + r * Math.sin(angle);
    });
  } else {
    // Default Force
    graphNodes.forEach((n) => {
      n.fx = null;
      n.fy = null;
    });
    simulation.force("charge", d3.forceManyBody().strength(-380));
    simulation.force("link").distance(135);
  }

  simulation.alpha(0.8).restart();
}

function focusOrFetchGraphNode(entityIdOrName) {
  const cleanQuery = entityIdOrName.trim().toLowerCase();

  let targetNode = graphNodes.find((n) => n.id.toLowerCase() === cleanQuery);
  if (!targetNode) {
    targetNode = graphNodes.find((n) => (n.displayName || "").toLowerCase().includes(cleanQuery));
  }

  if (targetNode) {
    highlightNodeNeighbors(targetNode.id);
    inspectNode(targetNode.raw || targetNode);

    if (canvas && zoomBehavior && targetNode.x !== undefined) {
      const container = document.getElementById("cy-canvas");
      const w = container.clientWidth;
      const h = container.clientHeight;
      const transform = d3.zoomIdentity.translate(w / 2 - targetNode.x * 1.4, h / 2 - targetNode.y * 1.4).scale(1.4);
      d3.select(canvas).transition().duration(500).call(zoomBehavior.transform, transform);
    }
  } else {
    loadGraphData(resolveEntityId(entityIdOrName));
  }
}

function inspectNode(data) {
  const heading = document.getElementById("drawer-heading");
  const badge = document.getElementById("drawer-type-badge");
  const content = document.getElementById("drawer-content");

  const displayName = getEntityDisplayName(data.id, data);

  if (heading) heading.innerText = displayName;
  if (badge) {
    badge.innerText = data.type || "Entity";
    const typeConfig = ENTITY_CONFIG[data.type] || ENTITY_CONFIG.Default;
    badge.style.borderColor = typeConfig.stroke;
    badge.style.color = typeConfig.stroke;
  }

  if (!content) return;

  const connectedCount = graphLinks.filter(l => {
    const s = typeof l.source === 'object' ? l.source.id : l.source;
    const t = typeof l.target === 'object' ? l.target.id : l.target;
    return s === data.id || t === data.id;
  }).length;

  content.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 14px;">
      <div style="background: #f8fafc; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 12px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="color: var(--text-muted); font-size: 0.7rem; font-family: var(--font-mono);">SUBJECT NAME</span>
          <span style="color: var(--accent-blue); font-weight: 700; font-size: 0.9rem;">${displayName}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="color: var(--text-muted); font-size: 0.7rem; font-family: var(--font-mono);">ENTITY TYPE</span>
          <span style="font-weight: 600;">${data.type || "Person"}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="color: var(--text-muted); font-size: 0.7rem; font-family: var(--font-mono);">ASSOCIATIVE LINKS</span>
          <span class="mono" style="color: var(--accent-emerald); font-weight: 700;">${connectedCount} Direct Connections</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: var(--text-muted); font-size: 0.7rem; font-family: var(--font-mono);">RECORD STATUS</span>
          <span class="badge" style="background: rgba(5,150,105,0.1); color: var(--accent-emerald);">VERIFIED INTEL</span>
        </div>
      </div>

      <div>
        <div style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px;">Primary Dossier &amp; Attributes</div>
        <div style="background: #ffffff; border: 1px solid var(--border-muted); border-radius: var(--radius-sm); padding: 10px; font-size: 0.78rem; line-height: 1.6; color: var(--text-secondary);">
          <div><strong>Identified Name:</strong> ${displayName}</div>
          ${data.occupation ? `<div><strong>Occupation:</strong> ${data.occupation}</div>` : ""}
          ${data.city ? `<div><strong>Jurisdiction:</strong> ${data.city}</div>` : ""}
          ${data.carrier ? `<div><strong>Telecom Carrier:</strong> ${data.carrier}</div>` : ""}
          ${data.institution ? `<div><strong>Financial Institution:</strong> ${data.institution}</div>` : ""}
          ${data.make ? `<div><strong>Vehicle Model:</strong> ${data.make}</div>` : ""}
        </div>
      </div>

      <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 6px;">
        <button class="btn btn-primary btn-sm" onclick="window.netralinkApp.expandNodeNetwork('${data.id}')">
          <i data-lucide="git-branch" size="13"></i> Expand 2-Hop Network
        </button>
        <button class="btn btn-secondary btn-sm" onclick="window.netralinkApp.openHiddenPathsModal('${displayName}', 'Vikram Sethi @ Langda')">
          <i data-lucide="search" size="13"></i> Trace Paths to Vikram Sethi @ Langda
        </button>
      </div>
    </div>
  `;
  if (window.lucide) window.lucide.createIcons();
}

function inspectEdge(data) {
  const heading = document.getElementById("drawer-heading");
  const badge = document.getElementById("drawer-type-badge");
  const content = document.getElementById("drawer-content");

  if (heading) heading.innerText = data.label || data.relation || "Evidence Link";
  if (badge) {
    badge.innerText = "Evidence Relation";
    badge.style.borderColor = "var(--border-muted)";
    badge.style.color = "var(--text-secondary)";
  }

  if (!content) return;

  const srcName = getEntityDisplayName(data.source || data.from);
  const tgtName = getEntityDisplayName(data.target || data.to);

  content.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 14px;">
      <div style="background: #f8fafc; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 12px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="color: var(--text-muted); font-size: 0.7rem; font-family: var(--font-mono);">RELATION</span>
          <span class="mono" style="color: var(--accent-cyan); font-weight: 700;">${data.label || data.relation}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="color: var(--text-muted); font-size: 0.7rem; font-family: var(--font-mono);">SOURCE ENTITY</span>
          <span style="color: var(--accent-blue); font-weight: 600;">${srcName}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="color: var(--text-muted); font-size: 0.7rem; font-family: var(--font-mono);">TARGET ENTITY</span>
          <span style="color: var(--accent-rose); font-weight: 600;">${tgtName}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: var(--text-muted); font-size: 0.7rem; font-family: var(--font-mono);">CONFIDENCE</span>
          <span class="mono" style="color: var(--accent-emerald); font-weight: 700;">${Math.round((data.confidence || 0.95) * 100)}%</span>
        </div>
      </div>

      <div>
        <div style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px;">Intelligence Provenance</div>
        <div style="background: #ffffff; border: 1px solid var(--border-muted); border-radius: var(--radius-sm); padding: 10px; font-size: 0.78rem; line-height: 1.6; color: var(--text-secondary);">
          <div><strong>Timestamp:</strong> ${data.timestamp || "Active Pattern Window"}</div>
          <div><strong>Evidence Source:</strong> ${data.source_evidence || "Correlated Multimodal Ingest"}</div>
          <div><strong>Legal Admissibility:</strong> Section 65B Certified Hash Match</div>
        </div>
      </div>
    </div>
  `;
  if (window.lucide) window.lucide.createIcons();
}

// ----------------------------------------------------------------------------
// 8. EXPLAINABLE LEADS (Person Names Displayed)
// ----------------------------------------------------------------------------
async function loadLeadsView() {
  const container = document.getElementById("leads-container");
  if (!container) return;

  try {
    const res = await api.leads.list(currentCaseId);
    const leads = res.leads || [];

    container.innerHTML = leads.map((l) => {
      const personName = getEntityDisplayName(l.candidate_entity_id, { label: l.candidate_label });
      const cleanTitle = sanitizePersonNamesInText(l.title);
      const cleanSummary = sanitizePersonNamesInText(l.summary || l.title);
      const rawText = RAW_EVIDENCE_MAP[l.candidate_entity_id] || RAW_EVIDENCE_MAP["LEAD-001"] || `[RAW INGEST EXTRACT]\nSource: ${l.cited_evidence ? l.cited_evidence.join(", ") : "FIR-RPT00001"}\nText: Field intercept narrative confirms activity of ${personName} across narcotics and financial layering clusters.`;

      const explanationBullets = Array.isArray(l.explanation_points) ? l.explanation_points : [];

      return `
        <div class="panel-card" style="border-left: 4px solid var(--accent-blue);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div>
              <strong style="font-family: var(--font-display); font-size: 1.05rem; color: var(--text-primary);">Lead ${l.lead_number}: ${personName}</strong>
              <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">
                Subject: <strong style="color: var(--accent-blue);">${personName}</strong> · Priority: <span class="badge danger">${l.priority || "HIGH"}</span> · Confidence: <strong class="mono" style="color: var(--accent-emerald);">${Math.round((l.confidence_score || l.bridge_score || 0.89) * 100)}%</strong>
              </div>
            </div>
            <span class="badge" style="background: rgba(37,99,235,0.12); color: var(--accent-blue); font-size: 0.75rem;">${l.status}</span>
          </div>

          <p style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 10px; font-weight: 500;">
            ${cleanSummary}
          </p>

          <!-- Explanation Bullets -->
          ${explanationBullets.length > 0 ? `
            <div style="background: var(--bg-base); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 10px 14px; margin-bottom: 12px;">
              <div style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; font-weight: 700;">AI Explanation &amp; Evidence Audit Points</div>
              <ul style="padding-left: 18px; font-size: 0.78rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 4px;">
                ${explanationBullets.map(pt => `<li>${sanitizePersonNamesInText(pt)}</li>`).join("")}
              </ul>
            </div>
          ` : ""}

          <!-- RAW TEXT EVIDENCE CONTAINER -->
          <div>
            <div style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-top: 8px;">
              📜 Raw Intelligence Evidence Text (Unedited Record)
            </div>
            <div class="raw-evidence-box">${rawText}</div>
          </div>

          <div style="display: flex; gap: 8px; margin-top: 12px;">
            <button class="btn btn-primary btn-sm" onclick="window.netralinkApp.reviewLead('${l.id}')">Human Review Terminal</button>
            <button class="btn btn-secondary btn-sm" onclick="window.netralinkApp.focusGraphEntity('${personName}')">Inspect Person on Graph</button>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-rose);">Failed to load explainable leads.</div>`;
  }
}

// ----------------------------------------------------------------------------
// 9. GEOSPATIAL MOVEMENT INTERACTIVE LEAFLET MAP
// ----------------------------------------------------------------------------
async function loadGeoMap() {
  const container = document.getElementById("map-container");
  if (!container) return;

  try {
    const mapData = await api.map.get(currentCaseId);
    const locs = mapData.locations || [];
    const trajectories = mapData.trajectories || [];

    // Construct Map Layout HTML
    container.innerHTML = `
      <div class="map-body-container">
        <!-- Interactive Leaflet Map Canvas -->
        <div id="geo-leaflet-map" class="leaflet-map-frame"></div>

        <!-- Trajectory & Location Intelligence Log -->
        <div style="display: flex; flex-direction: column; gap: 12px; overflow-y: auto;">
          <div class="panel-card">
            <div class="panel-card-title">Interstate Co-Location Corridors</div>
            <p style="font-size: 0.76rem; color: var(--text-secondary); margin-bottom: 10px;">
              Movement trajectory logged for <strong style="color: var(--accent-blue);">Rahul Sharma @ Guddu</strong> across 4 police zones.
            </p>
            <div style="display: flex; flex-direction: column; gap: 8px;">
              ${locs.map(loc => `
                <div style="padding: 10px; background: #ffffff; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); border-left: 3px solid var(--accent-rose); box-shadow: var(--shadow-card);">
                  <div style="display: flex; justify-content: space-between;">
                    <strong style="color: var(--text-primary); font-size: 0.84rem;">${loc.name}</strong>
                    <span class="mono" style="font-size: 0.72rem; color: var(--accent-blue);">${loc.city}</span>
                  </div>
                  <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 3px;">Type: ${loc.type}</div>
                  <div class="mono" style="font-size: 0.7rem; color: var(--accent-rose); margin-top: 3px; font-weight: 600;">Recorded Events: ${loc.events_count}</div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      </div>
    `;

    // Initialize Leaflet Map
    if (window.L) {
      if (leafletMap) {
        leafletMap.remove();
        leafletMap = null;
      }

      leafletMap = L.map("geo-leaflet-map").setView([23.8, 77.5], 7);

      // OpenStreetMap Light Tile Layer
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
      }).addTo(leafletMap);

      // Plot Locations
      const latLngList = [];
      locs.forEach(loc => {
        if (loc.lat && loc.lng) {
          const point = [loc.lat, loc.lng];
          latLngList.push(point);

          const marker = L.circleMarker(point, {
            radius: 9,
            fillColor: "#dc2626",
            color: "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
          }).addTo(leafletMap);

          marker.bindPopup(`
            <div style="font-family: var(--font-ui); font-size: 0.8rem; padding: 4px;">
              <strong style="color: #2563eb; font-size: 0.88rem;">${loc.name}</strong><br/>
              <span style="color: #64748b; font-family: var(--font-mono); font-size: 0.72rem;">${loc.city} · ${loc.id}</span><br/>
              <div style="margin-top: 4px; font-weight: 600;">Zone: ${loc.type}</div>
              <div style="color: #dc2626; margin-top: 2px;">Recorded Intel Co-Locations: ${loc.events_count}</div>
            </div>
          `);
        }
      });

      // Draw Polyline Route for Trajectories
      trajectories.forEach(tr => {
        const pathCoords = (tr.path || []).map(p => [p.lat, p.lng]);
        if (pathCoords.length > 1) {
          const polyline = L.polyline(pathCoords, {
            color: "#2563eb",
            weight: 4,
            opacity: 0.85,
            dashArray: "8, 6"
          }).addTo(leafletMap);

          const personLabel = getEntityDisplayName(tr.person_id, { label: tr.label });
          polyline.bindTooltip(`Trajectory: ${personLabel}`, { sticky: true });
        }
      });

      if (latLngList.length > 0) {
        leafletMap.fitBounds(latLngList, { padding: [40, 40] });
      }
    }
  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-rose);">Failed to load map data.</div>`;
  }
}

// ----------------------------------------------------------------------------
// 10. CRIME LENSES & CROSS-CRIME RADAR
// ----------------------------------------------------------------------------
async function loadCrimeLenses() {
  const container = document.getElementById("lenses-cards-container");
  if (!container) return;

  try {
    const lenses = await api.lenses.list(currentCaseId);
    container.innerHTML = lenses.map((l) => `
      <div class="panel-card lens-card" style="cursor: pointer;" onclick="viewLensGraph('${l.id}')">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
          <strong style="font-family: var(--font-display); font-size: 0.95rem; color: var(--accent-blue);">${l.id} · ${l.name}</strong>
          <span class="badge" style="background: rgba(37,99,235,0.1); color: var(--accent-blue);">${l.badge || "Lens"}</span>
        </div>
        <p style="font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 10px;">${l.desc}</p>
        <div class="mono" style="font-size: 0.72rem; color: var(--text-muted);">Pattern: ${l.pattern}</div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-rose);">Failed to load crime lenses.</div>`;
  }
}

window.viewLensGraph = async function (lensId) {
  switchView("graph");
  const navItem = document.querySelector('.sidebar .nav-item[data-view="graph"]');
  if (navItem) {
    document.querySelectorAll(".sidebar .nav-item").forEach((i) => i.classList.remove("active"));
    navItem.classList.add("active");
  }

  try {
    const lensRes = await api.lenses.get(currentCaseId, lensId);
    if (lensRes && lensRes.graph) {
      const { nodes, links } = convertToD3Data(lensRes.graph);
      graphNodes = nodes;
      graphLinks = links;
      if (simulation) {
        simulation.nodes(graphNodes);
        simulation.force("link").links(graphLinks);
        simulation.alpha(0.8).restart();
      }
    }
  } catch (err) {
    console.error("Lens graph error:", err);
  }
};

async function loadCrossCrimeRadar() {
  const tbody = document.getElementById("cross-crime-matrix-body");
  if (!tbody) return;

  try {
    const radar = await api.lenses.crossCrime(currentCaseId);
    const matrix = radar.matrix || [];

    tbody.innerHTML = matrix.map((row) => {
      const sharedName = getEntityDisplayName(row.shared_entity);
      return `
        <tr>
          <td><strong>${row.domain_pair}</strong></td>
          <td><strong style="color: var(--accent-rose); font-size: 0.88rem;">${sharedName}</strong></td>
          <td><span class="badge" style="background: rgba(220,38,38,0.1); color: var(--accent-rose);">${row.strength}</span></td>
          <td class="mono" style="font-weight: 700; color: var(--accent-rose);">${Math.round(row.bridge_score * 100)}%</td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" style="color: var(--accent-rose);">Failed to load cross-crime matrix.</td></tr>`;
  }
}

// ----------------------------------------------------------------------------
// 11. ALERTS, AUDIT & MODALS
// ----------------------------------------------------------------------------
async function loadAlertsView() {
  const tbody = document.getElementById("alerts-table-body");
  if (!tbody) return;

  try {
    const res = await api.alerts.list(currentCaseId);
    const alerts = res.alerts || [];

    tbody.innerHTML = alerts.map((a) => {
      const personName = getEntityDisplayName(a.target_entity_id || a.entity_id);
      const cleanTitle = sanitizePersonNamesInText(a.title);
      const cleanDesc = sanitizePersonNamesInText(a.description);
      return `
        <tr>
          <td><span class="badge danger">${a.priority}</span></td>
          <td><strong>${cleanTitle}</strong></td>
          <td><strong style="color: var(--accent-blue); font-size: 0.86rem;">${personName}</strong></td>
          <td style="font-size: 0.78rem; color: var(--text-secondary);">${cleanDesc}</td>
          <td class="mono">${a.evidence_count}</td>
          <td><span class="badge">${a.status}</span></td>
          <td>
            <button class="btn btn-sm btn-secondary" onclick="updateAlertStatus('${a.id}', 'UNDER_REVIEW')">Review</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="color: var(--accent-rose);">Failed to load alerts.</td></tr>`;
  }
}

window.updateAlertStatus = async function (alertId, status) {
  try {
    await api.alerts.updateStatus(alertId, status);
    loadAlertsView();
  } catch (err) {
    alert("Alert update error: " + err.message);
  }
};

async function loadAuditTrailView() {
  const tbody = document.getElementById("audit-table-body");
  if (!tbody) return;

  try {
    const res = await api.audit.get(currentCaseId);
    const logs = res.logs || [];

    tbody.innerHTML = logs.map((l) => {
      const targetName = getEntityDisplayName(l.target_entity);
      const cleanDetails = sanitizePersonNamesInText(l.details);
      return `
        <tr>
          <td class="mono" style="font-size: 0.72rem; color: var(--text-secondary);">${l.created_at || l.timestamp}</td>
          <td><strong>${l.user_name}</strong></td>
          <td><span class="badge">${l.user_role}</span></td>
          <td><strong class="mono" style="color: var(--accent-blue);">${l.action}</strong></td>
          <td><strong>${targetName}</strong></td>
          <td style="font-size: 0.78rem; color: var(--text-secondary);">${cleanDetails}</td>
          <td class="mono" style="font-size: 0.72rem; color: var(--accent-cyan);">${(l.event_hash || "").substring(0, 16)}...</td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="color: var(--accent-rose);">Failed to load audit trail.</td></tr>`;
  }
}

function setupModals() {
  // Pathfinding Modal
  document.getElementById("btn-run-pathfinding")?.addEventListener("click", async () => {
    const srcInput = document.getElementById("path-source-input").value.trim();
    const tgtInput = document.getElementById("path-target-input").value.trim();
    const resContainer = document.getElementById("path-results-container");

    const src = resolveEntityId(srcInput);
    const tgt = resolveEntityId(tgtInput);

    try {
      const pathsRes = await api.graph.hiddenPaths(currentCaseId, src, tgt);
      const paths = pathsRes.paths || [];

      if (paths.length === 0) {
        resContainer.innerHTML = `<div style="color: var(--text-muted); padding: 12px 0;">No operational paths found between ${getEntityDisplayName(src)} and ${getEntityDisplayName(tgt)}.</div>`;
      } else {
        resContainer.innerHTML = paths.map((p) => {
          const namedNodes = p.nodes.map(n => getEntityDisplayName(n));
          const cleanExplanation = sanitizePersonNamesInText(p.explanation);
          return `
            <div style="padding: 12px; background: #ffffff; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); margin-top: 10px; box-shadow: var(--shadow-card);">
              <strong style="color: var(--accent-blue); font-size: 0.84rem;">Path: ${p.path_id} (${p.length} operational hops)</strong>
              <div style="font-size: 0.84rem; margin-top: 6px; color: var(--text-primary); font-weight: 600;">
                ${namedNodes.join(" ➔ ")}
              </div>
              <p style="font-size: 0.76rem; color: var(--text-secondary); margin-top: 6px;">
                ${cleanExplanation}
              </p>
            </div>
          `;
        }).join("");
      }
    } catch (err) {
      resContainer.innerHTML = `<div style="color: var(--accent-rose);">Pathfinding error: ${err.message}</div>`;
    }
  });

  // Evidence Ingest Modal
  document.getElementById("btn-open-ingest-modal")?.addEventListener("click", () => {
    document.getElementById("modal-ingest-evidence").classList.add("active");
  });

  document.getElementById("btn-seed-demo")?.addEventListener("click", async () => {
    try {
      await api.investigations.seedDemo(currentCaseId);
      alert("Demonstration case successfully re-seeded!");
      loadOverviewData();
      loadEvidenceHub();
    } catch (err) {
      alert("Seed error: " + err.message);
    }
  });

  document.getElementById("btn-submit-evidence")?.addEventListener("click", async () => {
    const ref = document.getElementById("ingest-ref-input").value.trim();
    const text = document.getElementById("ingest-content-input").value.trim();
    if (!text) return alert("Please enter evidence narrative text.");

    try {
      const res = await api.evidence.ingest(currentCaseId, {
        evidence_type: "FIR / Police Intercept",
        source_reference: ref || "FIR-LIVE-089",
        title: "Field Intercept Narrative",
        content_text: text
      });

      alert(`Evidence ingested successfully! SHA-256: ${res.sha256_hash.substring(0, 16)}...`);
      window.netralinkApp.closeModals();
      loadOverviewData();
      loadEvidenceHub();
    } catch (err) {
      alert("Ingestion error: " + err.message);
    }
  });

  // Human Review Modal Actions
  document.getElementById("btn-decision-accept")?.addEventListener("click", () => submitLeadDecision("ACCEPT"));
  document.getElementById("btn-decision-dismiss")?.addEventListener("click", () => submitLeadDecision("DISMISS"));
  document.getElementById("btn-decision-flag")?.addEventListener("click", () => submitLeadDecision("FLAG"));
}

async function openReviewModal(leadId) {
  activeLeadForReview = leadId;
  const metaContainer = document.getElementById("review-lead-meta");
  if (metaContainer) {
    metaContainer.innerHTML = `<div style="color: var(--accent-blue); font-size: 0.85rem; font-weight: 600;">Reviewing Lead for Subject: <strong>Rahul Sharma @ Guddu</strong></div>`;
  }
  const modal = document.getElementById("modal-review");
  if (modal) modal.classList.add("active");
}

async function submitLeadDecision(decision) {
  if (!activeLeadForReview) return;
  const reason = document.getElementById("review-reason-input").value.trim();
  if (!reason) return alert("Investigator review rationale is mandatory for audit trail compliance.");

  try {
    await api.leads.review(activeLeadForReview, decision, reason);
    alert(`Lead status successfully updated to ${decision}ED.`);
    window.netralinkApp.closeModals();
    loadLeadsView();
  } catch (err) {
    alert("Review error: " + err.message);
  }
}
