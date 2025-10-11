export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:4000";

export async function fetchStats(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function updateStats(payload: any): Promise<any> {
  const res = await fetch(`${API_BASE}/api/stats`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to update stats: ${text}`);
  }
  return res.json();
}