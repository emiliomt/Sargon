from dataclasses import dataclass
from typing import Dict, List

import yfinance as yf


@dataclass
class RebalanceAction:
    ticker: str
    current_value: float
    current_pct: float
    target_pct: float
    drift: float
    action: str  # "BUY" | "SELL" | "HOLD"
    trade_value: float
    trade_shares: float


def _get_prices(tickers: List[str]) -> Dict[str, float]:
    prices: Dict[str, float] = {}
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period="1d")
            prices[ticker] = float(hist["Close"].iloc[-1]) if not hist.empty else 0.0
        except Exception:
            prices[ticker] = 0.0
    return prices


def calculate_rebalance(
    holdings: Dict[str, float],       # ticker -> shares
    target_allocation: Dict[str, float],  # ticker -> target %
    threshold: float = 5.0,
) -> List[RebalanceAction]:
    tickers = list(holdings.keys())
    prices = _get_prices(tickers)

    values = {t: holdings[t] * prices[t] for t in tickers}
    total = sum(values.values())
    if total == 0:
        return []

    actions: List[RebalanceAction] = []
    for ticker in tickers:
        current_val = values[ticker]
        current_pct = current_val / total * 100
        target_pct = target_allocation.get(ticker, 0.0)
        drift = current_pct - target_pct
        trade_val = (target_pct / 100 * total) - current_val
        price = prices[ticker]
        trade_shares = trade_val / price if price > 0 else 0.0

        if abs(drift) < threshold:
            action = "HOLD"
        elif drift > 0:
            action = "SELL"
        else:
            action = "BUY"

        actions.append(
            RebalanceAction(
                ticker=ticker,
                current_value=round(current_val, 2),
                current_pct=round(current_pct, 2),
                target_pct=round(target_pct, 2),
                drift=round(drift, 2),
                action=action,
                trade_value=round(abs(trade_val), 2),
                trade_shares=round(abs(trade_shares), 4),
            )
        )

    return sorted(actions, key=lambda a: abs(a.drift), reverse=True)
