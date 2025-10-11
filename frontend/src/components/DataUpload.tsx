import React, { useState } from "react";
import { updateStats } from "../services/api";

export default function DataUpload({ afterSubmit }: any) {
  const [text, setText] = useState<string>(""
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    setError(null); setSuccess(null);
    const f = e.target.files?.[0]; if (!f) return;
    const reader = new FileReader();
    reader.onload = () => setText(String(reader.result ?? ""));
    reader.readAsText(f);
  }

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault(); setError(null); setSuccess(null);
    let payload: any;
    try { payload = JSON.parse(text); } catch (err) { setError("Invalid JSON"); return; }
    setLoading(true);
    try { const res = await updateStats(payload); setSuccess("Uploaded"); afterSubmit?.(res); } catch (err: any) { setError(err.message); } finally { setLoading(false); }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <label style={{ fontSize: 13, color: "var(--muted)" }}>Upload dashboard data (JSON)</label>
      <div style={{ display: "flex", gap: 8 }}>
        <input type="file" accept=".json,application/json" onChange={handleFile} />
        <button type="button" className="btn small" onClick={() => setText(JSON.stringify({ mock: true }, null, 2))}>Paste sample</button>
        <button type="button" className="btn small" onClick={() => setText("")}>Clear</button>
      </div>
      <textarea value={text} onChange={(e) => setText(e.target.value)} rows={8} style={{ borderRadius: 8, padding: 10, background: "rgba(255,255,255,0.02)", color: "inherit" }} />
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <button className="btn primary" type="submit" disabled={loading || !text}>{loading ? "Uploading…" : "Upload & Apply"}</button>
        {error && <div style={{ color: "#ff9b9b" }}>{error}</div>}
        {success && <div style={{ color: "var(--accent)" }}>{success}</div>}
      </div>
    </form>
  );
}