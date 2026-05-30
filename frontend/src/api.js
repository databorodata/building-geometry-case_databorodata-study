// Minimal API client. Point at the backend; override with VITE_API_BASE if needed.
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function getHealth() {
  const res = await fetch(`${API_BASE}/api/v1/health`);
  if (!res.ok) throw new Error(`health check failed: ${res.status}`);
  return res.json();
}

// TODO(candidate): add the calls for your massing / options API here, e.g.
//   export async function createMassing(payload) { ... }
//   export async function branchOption(id, payload) { ... }
//   export async function listOptions() { ... }
