import React from "react";
import { useNavigate } from "react-router-dom";
import Header from "../ui/Header";
import "../styles/landing.css";

export default function Landing() {
  const nav = useNavigate();
  function openDashboard(view: "borrower" | "lender") {
    nav(`/dashboard?view=${view}`);
  }

  return (
    <div className="site landing-site">
      <Header sticky />
      <main className="landing-wrap">
        <section className="hero vintage-hero" aria-labelledby="hero-title">
          <div className="hero-left">
            <h1 id="hero-title" className="hero-title">
              Alpha Shield — lending reimagined with long-term alignment
            </h1>
            <p className="hero-sub">
              We combine continuous investment coverage, adaptive repayment intelligence, and
              human-centered recommendations to lower borrowing costs while keeping lenders secure.
              Simple, transparent, and built to serve both people and portfolios.
            </p>

            <div className="cta-row">
              <button
                className="btn primary large"
                onClick={() => openDashboard("borrower")}
                aria-label="Open Borrower Dashboard"
              >
                Enter Borrower Dashboard
              </button>

              <button
                className="btn ghost large"
                onClick={() => openDashboard("lender")}
                aria-label="Open Lender Dashboard"
              >
                Enter Lender Dashboard
              </button>
            </div>

            <div className="mission-summary">
              <h3>Our Mission</h3>
              <p>
                Make credit fairer and more dynamic by aligning lending with a borrower’s real
                financial activity and savings potential. We help people access better outcomes
                while lowering systemic credit risk.
              </p>
            </div>

            <div className="features-row" aria-hidden>
              <div className="feature-card">
                <strong>Lower Cost</strong>
                <div className="muted">Leverage investment coverage to cut interest paid.</div>
              </div>
              <div className="feature-card">
                <strong>Continuous Signals</strong>
                <div className="muted">Adaptive plans driven by real-time analytics.</div>
              </div>
              <div className="feature-card">
                <strong>Human-centered</strong>
                <div className="muted">Simple recommendations and transparent rules.</div>
              </div>
            </div>
          </div>

          <aside className="hero-right" aria-hidden>
            <div className="device-card">
              <div className="device-topbar" />
              <div className="device-canvas">
                <div className="mock-dashboard">
                  <div className="mock-row">
                    <div className="mock-card small" />
                    <div className="mock-card wide" />
                  </div>
                  <div className="mock-row">
                    <div className="mock-card tall" />
                    <div className="mock-card small" />
                  </div>
                </div>
              </div>
            </div>

            <div className="swatches">
              <div className="swatch accent">Accent</div>
              <div className="swatch primary">Primary</div>
              <div className="swatch warm">Warm</div>
              <div className="swatch paper">Paper</div>
            </div>
          </aside>
        </section>

        <section className="story" id="story">
          <div className="story-inner">
            <h2>Why Alpha Shield</h2>
            <p>
              Traditional lending is static — a single snapshot that rarely reflects a person’s
              true trajectory. Alpha Shield creates flexible loans that adapt to savings, investment
              performance, and spending behavior so borrowers pay less when they’re doing well and
              lenders receive better risk controls.
            </p>

            <div className="story-cards">
              <article className="story-card">
                <h4>Dynamic Coverage</h4>
                <p>Automatically apply investment returns to amortize payments when possible.</p>
              </article>
              <article className="story-card">
                <h4>Actionable Insights</h4>
                <p>Personalized tasks and nudges to improve financial health and reduce default risk.</p>
              </article>
              <article className="story-card">
                <h4>Built for Trust</h4>
                <p>Transparent rules, clear tradeoffs, and explainable decisions for both sides.</p>
              </article>
            </div>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <div>© " + new Date().getFullYear() + " Alpha Shield</div>
        <div className="muted">Built with care — lending aligned with people</div>
      </footer>
    </div>
  );
}