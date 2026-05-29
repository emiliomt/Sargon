from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize


@dataclass
class OptimizationResult:
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    efficient_frontier: List[Dict]


def _fetch_returns(tickers: List[str], period: str = "2y") -> pd.DataFrame:
    data = yf.download(tickers, period=period, auto_adjust=True, progress=False)
    closes = data["Close"] if len(tickers) > 1 else data["Close"].to_frame(name=tickers[0])
    return closes.dropna().pct_change().dropna()


def _portfolio_stats(
    weights: np.ndarray,
    mean_returns: pd.Series,
    cov: pd.DataFrame,
    rf: float,
):
    w = np.asarray(weights)
    ret = float(np.dot(w, mean_returns) * 252)
    vol = float(np.sqrt(w @ (cov.values * 252) @ w))
    sharpe = (ret - rf) / vol if vol > 0 else 0.0
    return ret, vol, sharpe


def optimize_portfolio(tickers: List[str], risk_free_rate: float = 0.05) -> OptimizationResult:
    returns = _fetch_returns(tickers)
    mean_ret = returns.mean()
    cov = returns.cov()
    n = len(tickers)
    x0 = np.full(n, 1.0 / n)
    bounds = [(0.01, 0.95)] * n
    sum_constraint = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

    result = minimize(
        lambda w: -_portfolio_stats(w, mean_ret, cov, risk_free_rate)[2],
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=[sum_constraint],
    )

    opt_w = result.x
    opt_ret, opt_vol, opt_sharpe = _portfolio_stats(opt_w, mean_ret, cov, risk_free_rate)

    # Build 20-point efficient frontier
    frontier: List[Dict] = []
    target_returns = np.linspace(mean_ret.min() * 252, mean_ret.max() * 252, 20)
    for target in target_returns:
        constr = [
            sum_constraint,
            {"type": "eq", "fun": lambda w, t=target: np.dot(w, mean_ret) * 252 - t},
        ]
        res = minimize(
            lambda w: _portfolio_stats(w, mean_ret, cov, risk_free_rate)[1],
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constr,
        )
        if res.success:
            _, vol, _ = _portfolio_stats(res.x, mean_ret, cov, risk_free_rate)
            frontier.append({"return": round(target * 100, 2), "volatility": round(vol * 100, 2)})

    return OptimizationResult(
        weights={t: round(float(w), 4) for t, w in zip(tickers, opt_w)},
        expected_return=round(opt_ret * 100, 2),
        volatility=round(opt_vol * 100, 2),
        sharpe_ratio=round(opt_sharpe, 3),
        efficient_frontier=frontier,
    )
