import React from "react";
import { Link } from "react-router-dom";
import { ViewMode } from "../pages/Dashboard";

type Props = { sticky?: boolean; view?: ViewMode; onChangeView?: (v: ViewMode) => void };

export default function Header({ sticky = false, view = "borrower", onChangeView }: Props) {
  return (
    <header className={`topbar ${sticky ? "sticky" : ""}`}> 
      <div className="brand">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path d="M12 2L3 6v6c0 5 3.9 9.7 9 10 5.1-.3 9-5 9-10V6l-9-4z" stroke="#4FD1A9" strokeWidth="1.2" fill="rgba(79,209,169,0.06)"/>
        </svg>
        <Link to="/" className="brand-link">Alpha Shield</Link>
      </div>

      <nav className="view-toggle" aria-label="View toggle">
        <button className={`btn small ${view === "lender" ? "" : "active"}`} onClick={() => onChangeView?.("borrower")} aria-pressed={view === "borrower"}>Borrower View</button>
        <button className={`btn small primary ${view === "lender" ? "active" : ""}`} onClick={() => onChangeView?.("lender")} aria-pressed={view === "lender"}>Lender View</button>
      </nav>

      <div className="top-actions">
        <Link to="/dashboard" className="btn small ghost">Open Dashboard</Link>
        <button className="icon-btn" title="Notifications">🔔</button>
      </div>
    </header>
  );
}