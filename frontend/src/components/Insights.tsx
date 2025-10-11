import React from "react";
export default function InsightsList({ insights }: any) {
  if (!insights || insights.length === 0) return <div className="muted small">No insights available.</div>;
  return (
    <div className="insights">
      {insights.map((ins: any, i: number) => (
        <div key={i} className={`insight ${ins.type === "suggestion" ? "suggestion" : ins.severity === "warning" ? "warning" : ""}`}> 
          <strong>{ins.title}</strong>
          <div style={{ marginTop: 6 }}><small>{ins.description}</small></div>
          {ins.meta && <div style={{ marginTop: 8 }} className="muted small">{ins.meta}</div>}
        </div>
      ))}
    </div>
  );
}