/**
 * NetraLink AI: Frontend Controller & Cytoscape Graph Visualizer
 */

let cy = null;
let currentLens = "07";
let isPlayingTimeline = false;
let timelineInterval = null;

// Sample Templates for Live Ingestion
const SAMPLES = {
  en: "On 2026-07-25, the record noted that PERSON_00561 was observed with PERSON_00975 near Zone_0123 in Ujjain. The note references phone PH01018, account ACC00481, and vehicle VEH00359. Available records indicate suspicious activity in time window.",
  hi: "PERSON_00151 और PERSON_00985 ने मिला, Zone_0178, Gwalior के पास। समय 2026-04-05 11:39:00.",
  ta: "PERSON_00788 और PERSON_00510 ने பணம் அனுப்பினார், Zone_0110, Indore के पास। समय 2026-03-04 14:53:00.",
  ur: "PERSON_00811 और PERSON_00637 ने رابطہ کیا, Zone_0051, Bhopal کے पास। समय 2026-08-30 11:56:00."
};

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  initCytoscape();
  setupEventListeners();
  loadInitialGraph();
  fetchSystemStats();
});

// ----------------------------------------------------------------------------
// 1. CYTOSCAPE GRAPH INITIALIZATION
// ----------------------------------------------------------------------------
function initCytoscape() {
  cy = cytoscape({
    container: document.getElementById("cy"),
    boxSelectionEnabled: false,
    autounselectify: false,
    style: [
      // Node Default Style
      {
        selector: "node",
        style: {
          "label": "data(label)",
          "color": "#e2e8f0",
          "font-family": "Outfit, sans-serif",
          "font-size": "11px",
          "text-valign": "bottom",
          "text-margin-y": "5px",
          "background-color": "data(color)",
          "width": 34,
          "height": 34,
          "border-width": 2,
          "border-color": "#ffffff",
          "border-opacity": 0.25,
          "transition-property": "background-color, border-color, width, height",
          "transition-duration": "0.3s"
        }
      },
      // Entity Specific Styles
      {
        selector: "node[type = 'Person']",
        style: { "background-color": "#3B82F6", "width": 40, "height": 40 }
      },
      {
        selector: "node[type = 'Phone']",
        style: { "background-color": "#10B981", "width": 28, "height": 28 }
      },
      {
        selector: "node[type = 'Account']",
        style: { "background-color": "#F59E0B", "width": 28, "height": 28 }
      },
      {
        selector: "node[type = 'Vehicle']",
        style: { "background-color": "#8B5CF6", "width": 30, "height": 30 }
      },
      {
        selector: "node[type = 'Location']",
        style: { "background-color": "#EF4444", "width": 32, "height": 32 }
      },
      // Highlighted / Selected Node
      {
        selector: "node:selected, node.highlighted",
        style: {
          "border-width": 4,
          "border-color": "#38BDF8",
          "border-opacity": 1.0,
          "box-shadow": "0 0 16px #38BDF8",
          "width": 46,
          "height": 46
        }
      },
      // Edge Default Style
      {
        selector: "edge",
        style: {
          "width": 1.8,
          "line-color": "rgba(255, 255, 255, 0.15)",
          "target-arrow-color": "rgba(255, 255, 255, 0.25)",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          "arrow-scale": 0.9,
          "opacity": 0.7
        }
      },
      // Highlighted / Selected Edge
      {
        selector: "edge.highlighted, edge:selected",
        style: {
          "width": 3.2,
          "line-color": "#38BDF8",
          "target-arrow-color": "#38BDF8",
          "opacity": 1.0,
          "label": "data(label)",
          "font-size": "9px",
          "color": "#94A3B8",
          "text-background-color": "#0F172A",
          "text-background-opacity": 0.8,
          "text-background-padding": "3px"
        }
      }
    ],
    layout: { name: "cose", animate: false }
  });

  // Node Click Listener
  cy.on("tap", "node", (evt) => {
    const node = evt.target;
    cy.elements().removeClass("highlighted");
    node.addClass("highlighted");
    node.neighborhood().addClass("highlighted");
    displayNodeInspector(node.data());
  });

  // Edge Click Listener
  cy.on("tap", "edge", (evt) => {
    const edge = evt.target;
    cy.elements().removeClass("highlighted");
    edge.addClass("highlighted");
    displayEdgeInspector(edge.data());
  });

  // Canvas Tap (Deselect)
  cy.on("tap", (evt) => {
    if (evt.target === cy) {
      cy.elements().removeClass("highlighted");
    }
  });
}

// ----------------------------------------------------------------------------
// 2. DATA FETCHING & GRAPH RENDERING
// ----------------------------------------------------------------------------
async function loadInitialGraph() {
  try {
    const res = await fetch("/api/lenses/07");
    const data = await res.json();
    renderGraphData(data.graph);
  } catch (err) {
    console.error("Failed to load initial graph:", err);
  }
}

async function fetchSystemStats() {
  try {
    const res = await fetch("/api/graph/stats");
    const stats = await res.json();
    document.getElementById("stat-nodes").innerText = stats.total_nodes.toLocaleString();
    document.getElementById("stat-edges").innerText = stats.total_edges.toLocaleString();
  } catch (err) {
    console.warn("Stats fetch skipped:", err);
  }
}

function renderGraphData(graphData, layoutName = null) {
  if (!cy) return;
  cy.elements().remove();
  cy.add(graphData);

  const selectedLayout = layoutName || document.getElementById("select-layout").value;
  runLayout(selectedLayout);
}

function runLayout(layoutName) {
  const options = {
    name: layoutName,
    animate: true,
    animationDuration: 600,
    fit: true,
    padding: 40
  };
  if (layoutName === "cose") {
    options.idealEdgeLength = 60;
    options.nodeOverlap = 20;
    options.randomize = false;
  }
  cy.layout(options).run();
}

// ----------------------------------------------------------------------------
// 3. EVENT LISTENERS & CONTROLS
// ----------------------------------------------------------------------------
function setupEventListeners() {
  // 7 Crime Lenses
  document.querySelectorAll(".lens-tab").forEach((btn) => {
    btn.addEventListener("click", async () => {
      document.querySelectorAll(".lens-tab").forEach((t) => t.classList.remove("active"));
      btn.classList.add("active");
      currentLens = btn.dataset.lens;

      try {
        const res = await fetch(`/api/lenses/${currentLens}`);
        const data = await res.json();
        renderGraphData(data.graph);
      } catch (err) {
        console.error("Lens error:", err);
      }
    });
  });

  // Toolbar Buttons
  document.getElementById("btn-zoom-in").addEventListener("click", () => {
    cy.zoom(cy.zoom() * 1.25);
  });
  document.getElementById("btn-zoom-out").addEventListener("click", () => {
    cy.zoom(cy.zoom() * 0.8);
  });
  document.getElementById("btn-fit").addEventListener("click", () => {
    cy.fit(null, 40);
  });
  document.getElementById("btn-relayout").addEventListener("click", () => {
    runLayout(document.getElementById("select-layout").value);
  });
  document.getElementById("select-layout").addEventListener("change", (e) => {
    runLayout(e.target.value);
  });

  // Search Node
  document.getElementById("btn-search").addEventListener("click", focusSearchNode);
  document.getElementById("input-search").addEventListener("keypress", (e) => {
    if (e.key === "Enter") focusSearchNode();
  });

  // Temporal Timeline Slider
  const slider = document.getElementById("timeline-slider");
  const display = document.getElementById("timeline-display");

  slider.addEventListener("input", (e) => {
    filterGraphByTime(parseInt(e.target.value));
  });

  document.getElementById("btn-timeline-play").addEventListener("click", toggleTimelinePlay);

  // Modals Open/Close
  setupModals();
}

function focusSearchNode() {
  const query = document.getElementById("input-search").value.trim();
  if (!query) return;

  const node = cy.getElementById(query);
  if (node.length > 0) {
    cy.elements().removeClass("highlighted");
    node.addClass("highlighted");
    node.neighborhood().addClass("highlighted");
    cy.animate({ center: { eles: node }, zoom: 1.8 }, { duration: 500 });
    displayNodeInspector(node.data());
  } else {
    // If not on canvas, fetch subgraph from backend
    fetch(`/api/graph/subgraph?entity_id=${encodeURIComponent(query)}&hops=2`)
      .then((res) => res.json())
      .then((graphData) => {
        if (graphData.nodes.length > 0) {
          renderGraphData(graphData);
          setTimeout(() => {
            const newNode = cy.getElementById(query);
            if (newNode.length) {
              newNode.addClass("highlighted");
              displayNodeInspector(newNode.data());
            }
          }, 600);
        } else {
          alert(`Entity ${query} not found.`);
        }
      });
  }
}

// ----------------------------------------------------------------------------
// 4. TEMPORAL TIMELINE SCRUBBER
// ----------------------------------------------------------------------------
function filterGraphByTime(dayOffset) {
  // Day offset 1 to 240 maps roughly Jan 01 2026 to Aug 31 2026
  const baseDate = new Date("2026-01-01T00:00:00");
  const targetDate = new Date(baseDate.getTime() + dayOffset * 24 * 60 * 60 * 1000);
  const dateStr = targetDate.toISOString().split("T")[0];

  document.getElementById("timeline-display").innerText = `Filtering Evidence up to: ${dateStr}`;

  // Filter edges
  cy.edges().forEach((edge) => {
    const ts = edge.data("timestamp");
    if (!ts) {
      edge.style("display", "element");
    } else if (ts.split(" ")[0] <= dateStr) {
      edge.style("display", "element");
    } else {
      edge.style("display", "none");
    }
  });
}

function toggleTimelinePlay() {
  const playBtn = document.getElementById("btn-timeline-play");
  const slider = document.getElementById("timeline-slider");

  if (isPlayingTimeline) {
    clearInterval(timelineInterval);
    isPlayingTimeline = false;
    playBtn.innerText = "▶";
  } else {
    isPlayingTimeline = true;
    playBtn.innerText = "⏸";
    if (parseInt(slider.value) >= 240) slider.value = 1;

    timelineInterval = setInterval(() => {
      let val = parseInt(slider.value) + 5;
      if (val > 240) {
        val = 240;
        clearInterval(timelineInterval);
        isPlayingTimeline = false;
        playBtn.innerText = "▶";
      }
      slider.value = val;
      filterGraphByTime(val);
    }, 400);
  }
}

// ----------------------------------------------------------------------------
// 5. INSPECTOR DRAWER
// ----------------------------------------------------------------------------
function displayNodeInspector(data) {
  const type = data.type || "Entity";
  document.getElementById("inspector-type").innerText = `${type} Node`;

  let html = `
    <div class="inspect-card">
      <div class="card-title">${data.label || data.id}</div>
      <div class="card-subtitle">ID: ${data.id} · Type: ${type}</div>
      <div class="inspect-row"><span class="label">Occupation:</span><span class="val">${data.occupation || "N/A"}</span></div>
      <div class="inspect-row"><span class="label">Carrier / Bank:</span><span class="val">${data.carrier || data.institution || "N/A"}</span></div>
      <div class="inspect-row"><span class="label">Home Zone:</span><span class="val">${data.home_location || data.city || "N/A"}</span></div>
    </div>
  `;

  // If Person, show AI Lead Card
  if (type === "Person") {
    html += `
      <div class="lead-box">
        <div class="lead-title">AI Intelligence Lead</div>
        <div class="lead-text">
          Subject is flagged across <strong>${currentLens === "07" ? "Multiple Crime Archetypes" : "Current Crime Lens"}</strong>.
          Identified direct links to active operational assets and associates.
        </div>
      </div>
      <div style="margin-top: 16px;">
        <button class="btn btn-secondary btn-small" style="width: 100%;" onclick="expandNode('${data.id}')">
          Expand 2-Hop Network
        </button>
      </div>
    `;
  }

  document.getElementById("inspector-content").innerHTML = html;
}

function displayEdgeInspector(data) {
  document.getElementById("inspector-type").innerText = "Evidence Edge";
  const html = `
    <div class="inspect-card">
      <div class="card-title">${data.label || data.relation}</div>
      <div class="card-subtitle">Source: ${data.source} ➔ Target: ${data.target}</div>
      <div class="inspect-row"><span class="label">Timestamp:</span><span class="val">${data.timestamp || "Permanent"}</span></div>
      <div class="inspect-row"><span class="label">Confidence:</span><span class="val">${Math.round((data.confidence || 1.0) * 100)}%</span></div>
      <div class="inspect-row"><span class="label">Record ID:</span><span class="val">${data.source_id || "FIR_SYSTEM"}</span></div>
    </div>
  `;
  document.getElementById("inspector-content").innerHTML = html;
}

function expandNode(nodeId) {
  fetch(`/api/graph/subgraph?entity_id=${nodeId}&hops=2`)
    .then((res) => res.json())
    .then((graphData) => renderGraphData(graphData));
}

// ----------------------------------------------------------------------------
// 6. MODALS & REAL-TIME INGESTION
// ----------------------------------------------------------------------------
function setupModals() {
  // Ingest Modal
  const modalIngest = document.getElementById("modal-ingest");
  document.getElementById("btn-open-ingest").addEventListener("click", () => {
    modalIngest.classList.add("active");
  });
  document.getElementById("btn-close-ingest").addEventListener("click", () => {
    modalIngest.classList.remove("active");
  });

  // Sample Buttons
  document.querySelectorAll(".pill-sample").forEach((pill) => {
    pill.addEventListener("click", () => {
      document.getElementById("ingest-textarea").value = SAMPLES[pill.dataset.sample];
    });
  });

  // Submit Ingest
  document.getElementById("btn-submit-ingest").addEventListener("click", async () => {
    const text = document.getElementById("ingest-textarea").value.trim();
    if (!text) return alert("Please enter record text.");

    try {
      const res = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();

      document.getElementById("ingest-result").style.display = "block";
      document.getElementById("ingest-result-json").innerText = JSON.stringify(data.extracted_event, null, 2);

      // Render updated subgraph
      if (data.subgraph) {
        renderGraphData(data.subgraph);
        modalIngest.classList.remove("active");
      }
    } catch (err) {
      alert("Ingestion error: " + err.message);
    }
  });

  // Bridges Modal
  const modalBridges = document.getElementById("modal-bridges");
  document.getElementById("btn-open-bridges").addEventListener("click", async () => {
    modalBridges.classList.add("active");
    const res = await fetch("/api/analytics/bridge-entities");
    const data = await res.json();
    renderBridgesTable(data.bridges);
  });
  document.getElementById("btn-close-bridges").addEventListener("click", () => {
    modalBridges.classList.remove("active");
  });

  // Anomalies Modal
  const modalAnomalies = document.getElementById("modal-anomalies");
  document.getElementById("btn-open-anomalies").addEventListener("click", async () => {
    modalAnomalies.classList.add("active");
    const res = await fetch("/api/analytics/anomalies");
    const data = await res.json();
    renderAnomaliesTable(data.anomalies);
  });
  document.getElementById("btn-close-anomalies").addEventListener("click", () => {
    modalAnomalies.classList.remove("active");
  });
}

function renderBridgesTable(bridges) {
  let html = `
    <table>
      <thead>
        <tr>
          <th>Suspect ID</th>
          <th>Name</th>
          <th>Bridge Score</th>
          <th>Bridged Domains</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
  `;
  bridges.forEach((b) => {
    html += `
      <tr>
        <td><strong>${b.entity_id}</strong></td>
        <td>${b.label}</td>
        <td><span class="badge">${Math.round(b.bridge_score * 100)}%</span></td>
        <td>${b.communities_bridged} Crime Clusters</td>
        <td>
          <button class="btn btn-small" onclick="viewSuspectOnGraph('${b.entity_id}')">Investigate</button>
        </td>
      </tr>
    `;
  });
  html += `</tbody></table>`;
  document.getElementById("bridges-table-container").innerHTML = html;
}

function renderAnomaliesTable(anomalies) {
  let html = `
    <table>
      <thead>
        <tr>
          <th>TX ID</th>
          <th>From Account (Owner)</th>
          <th>To Account (Owner)</th>
          <th>Amount</th>
          <th>Risk Score</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
  `;
  anomalies.forEach((a) => {
    html += `
      <tr>
        <td><strong>${a.transaction_id}</strong></td>
        <td>${a.from_account} (${a.from_owner})</td>
        <td>${a.to_account} (${a.to_owner})</td>
        <td style="color: #F59E0B; font-weight: 600;">${a.amount_formatted}</td>
        <td><span class="badge" style="color: #F43F5E;">${Math.round(a.risk_score * 100)}%</span></td>
        <td>
          <button class="btn btn-small" onclick="viewSuspectOnGraph('${a.from_account}')">Trace Flow</button>
        </td>
      </tr>
    `;
  });
  html += `</tbody></table>`;
  document.getElementById("anomalies-table-container").innerHTML = html;
}

window.viewSuspectOnGraph = function (entityId) {
  document.querySelectorAll(".modal-overlay").forEach((m) => m.classList.remove("active"));
  document.getElementById("input-search").value = entityId;
  focusSearchNode();
};
