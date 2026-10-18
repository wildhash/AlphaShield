from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from alphashield.execution.bridge import evaluate_portfolio_feasibility

app = FastAPI(
    title="AlphaShield Autonomous Credit Core",
    description="Orchestration API for Gemini 3 and Lumibot integration loops.",
)


class LoanRequest(BaseModel):
    user_id: str
    requested_amount: float
    current_market_apr: float = 24.0


@app.get("/")
def read_root():
    return {"status": "operational", "engine": "Gemini 3 + Lumibot Integration"}


@app.post("/api/v1/originate")
async def originate_loan(request: LoanRequest):
    try:
        # 60/40 Split computation
        lending_pool = request.requested_amount * 0.60
        investment_pool = request.requested_amount * 0.40

        # Execute Lumibot Backtest loop via our internal tool structural bridge
        # Simulated standard low-drawdown allocation for the proof-of-concept sprint
        assets = ["SPY", "GLD", "TLT"]
        metrics = evaluate_portfolio_feasibility(assets, investment_pool)

        target_subsidized_apr = 8.0 if metrics["feasible"] else 14.0

        # Only expose safe summary fields — not the raw metrics dict
        telemetry_summary = {
            "feasible": bool(metrics.get("feasible")),
            "sharpe_ratio": float(metrics.get("sharpe_ratio", 0)),
            "max_drawdown": float(metrics.get("max_drawdown", 0)),
        }

        return {
            "user_id": request.user_id,
            "loan_allocation": {
                "lending_principal_60": lending_pool,
                "collateral_portfolio_40": investment_pool,
            },
            "backtest_telemetry": telemetry_summary,
            "adjusted_apr": target_subsidized_apr,
            "status": "Approved" if metrics["feasible"] else "Review Required",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc
