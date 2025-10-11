import React, { useMemo, useState, useEffect } from "react";
import Header from "../ui/Header";
import Card from "../ui/Card";
import { useSearchParams } from "react-router-dom";
import DataUpload from "../components/DataUpload";
import InsightsList from "../components/Insights";
import { useStats } from "../hooks/useStats";

export type ViewMode = "borrower" | "lender";

export default function Dashboard() {
  const { data: stats, isLoading } = useStats();
  const [searchParams] = useSearchParams();
  const initialView = (searchParams.get("view") as ViewMode) || "borrower";
  const [view, setView] = useState<ViewMode>(initialView);

  useEffect(() => {
    setView(initialView);
  }, [initialView]);

  if (isLoading) return <div style={{ padding: 28 }}>Loading...</div>;

  return (
    <div className="site">
      <Header view={view} onChangeView={(v) => setView(v)} />
      <main className="canvas">
        <Card title="Quick Stats" area="qs">
          <div className="stats-grid">
            <div className="stat">
              <small>Available Cash</small>
              <div className="stat-value">{stats.quick.cash}</div>
            </div>
            <div className="stat">
              <small>Savings</small>
              <div className="stat-value">{stats.quick.savings}</div>
            </div>
            <div className="stat">
              <small>Total Debt</small>
              <div className="stat-value">{stats.quick.debt}</div>
              <small className="muted">from {stats.quick.previousDebt}</small>
            </div>
            <div className="stat highlight">
              <small>Net Worth</small>
              <div className="stat-value green">{stats.quick.netWorth}</div>
            </div>
          </div>
        </Card>

        <Card title="Financial Health Score" area="fh" tall>
          <div className="score-row">
            <div className="donut">Good</div>
            <div className="scores">
              {stats.health.lines.map((l: any) => (
                <div key={l.label} className="score-line">
                  <small>{l.label}</small>
                  <div className="bar">
                    <div className="bar-fill" style={{ width: `${l.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card title="This Month's Spending" area="spend">
          {stats.spending.map((s: any) => (
            <div key={s.label} className="spend-line">
              <small>{s.label}</small>
              <div className="bar" style={{ flex: 1 }}>
                <div className={`bar-fill ${s.color ?? ""}`} style={{ width: `${s.pct}%` }} />
              </div>
              <div className="muted">{s.amount}</div>
            </div>
          ))}
          <div className="burn">
            Burn Rate <div className="burn-value">{stats.burn}</div>
          </div>
        </Card>

        <Card title={view === "borrower" ? "Spending Insights" : "Lender Insights"} area="insight">
          <InsightsList insights={(stats.__insights || [])} view={view} />
        </Card>

        <Card title="Data Upload (Admin)" area="upload">
          <DataUpload afterSubmit={() => { alert("Data uploaded — refresh will apply."); }} />
        </Card>

        <Card title="Goals Progress" area="goals">
          {stats.goals.map((g: any) => (
            <div className="goal" key={g.title}>
              <small>
                {g.title} <span className={`badge ${g.status === "ontrack" ? "ontrack" : "behind"}`}>{g.status === "ontrack" ? "On Track" : "Behind"}</span>
              </small>
              <div className="bar">
                <div className="bar-fill" style={{ width: `${g.pct}%` }} />
              </div>
              <div className="muted">{g.current} / {g.target}</div>
            </div>
          ))}
        </Card>

        <Card title="Action Items" area="actions">
          <div className="actions-list">
            {stats.actions.map((a: any) => (
              <div className="action" key={a.id}>
                <input type="checkbox" defaultChecked={a.done} />
                <span>{a.title}</span>
                <small className="muted" style={{ marginLeft: "auto" }}>{a.note}</small>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Portfolio Holdings" area="portfolio" wide>
          <table className="holdings">
            <thead><tr><th>Symbol</th><th>Shares</th><th>Value</th><th>P&L</th></tr></thead>
            <tbody>
              {stats.portfolio.map((p: any) => (
                <tr key={p.symbol}>
                  <td>{p.symbol}</td>
                  <td>{p.shares}</td>
                  <td>{p.value}</td>
                  <td className={p.pnl.startsWith("+") ? "green" : ""}>{p.pnl}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </main>
    </div>
  );
}