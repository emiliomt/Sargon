from datetime import date
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from portfolio_optimizer import optimize_portfolio
from rebalancer import calculate_rebalance
from risk_profiler import RISK_QUESTIONS, calculate_risk_profile
from tax_optimizer import HoldingInfo, analyze_tax_loss_opportunities

app = FastAPI(title="Sargon Investment Advisor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class RiskAnswers(BaseModel):
    answers: Dict[str, int]


class OptimizeRequest(BaseModel):
    tickers: List[str]
    risk_free_rate: float = 0.05


class HoldingItem(BaseModel):
    ticker: str
    shares: float
    cost_basis: float
    purchase_date: date


class TaxRequest(BaseModel):
    holdings: List[HoldingItem]


class RebalanceRequest(BaseModel):
    holdings: Dict[str, float]       # ticker -> shares
    target_allocation: Dict[str, float]  # ticker -> %
    threshold: float = 5.0


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Sargon Investment Advisor API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/risk-questions")
def get_risk_questions():
    return {"questions": RISK_QUESTIONS}


@app.post("/risk-profile")
def create_risk_profile(req: RiskAnswers):
    try:
        profile = calculate_risk_profile(req.answers)
        return {
            "score": profile.score,
            "category": profile.category,
            "description": profile.description,
            "suggested_allocation": profile.suggested_allocation,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/optimize")
def optimize(req: OptimizeRequest):
    if len(req.tickers) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 tickers")
    try:
        result = optimize_portfolio(req.tickers, req.risk_free_rate)
        return {
            "weights": result.weights,
            "expected_return": result.expected_return,
            "volatility": result.volatility,
            "sharpe_ratio": result.sharpe_ratio,
            "efficient_frontier": result.efficient_frontier,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/tax-optimize")
def tax_optimize(req: TaxRequest):
    try:
        holdings = [
            HoldingInfo(
                ticker=h.ticker,
                shares=h.shares,
                cost_basis=h.cost_basis,
                purchase_date=h.purchase_date,
            )
            for h in req.holdings
        ]
        suggestions = analyze_tax_loss_opportunities(holdings)
        return {
            "suggestions": [
                {
                    "ticker": s.ticker,
                    "current_price": s.current_price,
                    "cost_basis": s.cost_basis,
                    "unrealized_loss": s.unrealized_loss,
                    "loss_pct": s.loss_pct,
                    "action": s.action,
                    "replacement_tickers": s.replacement_tickers,
                    "wash_sale_warning": s.wash_sale_warning,
                }
                for s in suggestions
            ]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/rebalance")
def rebalance(req: RebalanceRequest):
    alloc_sum = sum(req.target_allocation.values())
    if abs(alloc_sum - 100) > 0.5:
        raise HTTPException(
            status_code=400,
            detail=f"Target allocation must sum to 100% (got {alloc_sum:.1f}%)",
        )
    try:
        actions = calculate_rebalance(req.holdings, req.target_allocation, req.threshold)
        return {
            "actions": [
                {
                    "ticker": a.ticker,
                    "current_value": a.current_value,
                    "current_pct": a.current_pct,
                    "target_pct": a.target_pct,
                    "drift": a.drift,
                    "action": a.action,
                    "trade_value": a.trade_value,
                    "trade_shares": a.trade_shares,
                }
                for a in actions
            ]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
