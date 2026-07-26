const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request(path, options) {
  const res = await fetch(`${API_BASE}/api/v1${path}`, options);
  if (!res.ok) {
    let message = `request failed: ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail?.message) message = body.detail.message;
      else if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail) && body.detail[0]?.msg) message = body.detail[0].msg;
    } catch {}
    throw new Error(message);
  }
  if (res.status === 204) return null;
  return res.json();
}

function post(path, payload) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getHealth() {
  return request("/health");
}

export async function previewMassing(polygon, params) {
  return post("/massing/preview", { polygon, params });
}

export async function createSite(name, polygon) {
  return post("/sites", { name, polygon });
}

export async function createOption(siteId, parentId, sourceId, name, params, kind = "save") {
  return post(`/sites/${siteId}/options`, { parent_id: parentId, source_id: sourceId, name, params, kind });
}

export async function deleteOption(optionId) {
  return request(`/options/${optionId}`, { method: "DELETE" });
}

export async function compareOptions(leftId, rightId) {
  return request(`/options/${leftId}/compare/${rightId}`);
}
