/**
 * NetraLink AI: Typed REST API Client
 * Connects frontend UI components directly to backend endpoints.
 */

const API_BASE = "";

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: { "Content-Type": "application/json" },
    ...options
  };
  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP error ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`[API Error] ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  auth: {
    login: (role = "Senior Investigator") => request("/api/auth/login", { method: "POST", body: JSON.stringify({ role }) }),
    me: () => request("/api/auth/me")
  },
  investigations: {
    list: () => request("/api/investigations"),
    get: (id) => request(`/api/investigations/${id}`),
    create: (data) => request("/api/investigations", { method: "POST", body: JSON.stringify(data) }),
    seedDemo: (id = "INV-ECLIPSE-2026") => request(`/api/investigations/${id}/demo-seed`, { method: "POST" })
  },
  evidence: {
    list: (invId) => request(`/api/investigations/${invId}/evidence`),
    ingest: (invId, data) => request(`/api/investigations/${invId}/evidence`, { method: "POST", body: JSON.stringify(data) })
  },
  pipeline: {
    run: (invId) => request(`/api/investigations/${invId}/pipeline/run`, { method: "POST" }),
    status: (invId) => request(`/api/investigations/${invId}/pipeline/status`)
  },
  entities: {
    list: (invId) => request(`/api/investigations/${invId}/entities`),
    candidates: (invId) => request(`/api/investigations/${invId}/entities/resolution/candidates`),
    decide: (invId, candidate_id, decision, notes = "") => 
      request(`/api/investigations/${invId}/entities/resolution/decide`, {
        method: "POST",
        body: JSON.stringify({ candidate_id, decision, notes })
      })
  },
  graph: {
    get: (invId, entityId = "P00561", hops = 2, start = null, end = null) => {
      let q = `/api/investigations/${invId}/graph?entity_id=${encodeURIComponent(entityId)}&hops=${hops}`;
      if (start) q += `&start_time=${start}`;
      if (end) q += `&end_time=${end}`;
      return request(q);
    },
    expand: (invId, entityId, hops = 1) => request(`/api/investigations/${invId}/graph/expand?entity_id=${encodeURIComponent(entityId)}&hops=${hops}`),
    hiddenPaths: (invId, src = "P00561", tgt = "P00151") => request(`/api/investigations/${invId}/graph/hidden-paths?source_id=${encodeURIComponent(src)}&target_id=${encodeURIComponent(tgt)}`)
  },
  lenses: {
    list: (invId) => request(`/api/investigations/${invId}/lenses`),
    get: (invId, lensId) => request(`/api/investigations/${invId}/lenses/${lensId}`),
    crossCrime: (invId) => request(`/api/investigations/${invId}/cross-crime`)
  },
  leads: {
    list: (invId) => request(`/api/investigations/${invId}/leads`),
    review: (leadId, decision, reason, reviewer = "Insp. A. K. Singh") => 
      request(`/api/leads/${leadId}/review`, {
        method: "POST",
        body: JSON.stringify({ decision, reason, reviewer_name: reviewer })
      })
  },
  alerts: {
    list: (invId) => request(`/api/investigations/${invId}/alerts`),
    updateStatus: (alertId, status) => request(`/api/alerts/${alertId}/status`, { method: "POST", body: JSON.stringify({ status }) })
  },
  map: {
    get: (invId) => request(`/api/investigations/${invId}/map`)
  },
  audit: {
    get: (invId) => request(`/api/investigations/${invId}/audit`)
  }
};
