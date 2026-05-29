from dataclasses import dataclass
from datetime import date
from typing import Dict, List

import yfinance as yf

# Broad-market substitutes to avoid wash-sale rule (30-day window)
_SUBSTITUTES: Dict[str, List[str]] = {
    "SPY": ["IVV", "VOO"],
    "IVV": ["SPY", "VOO"],
    "VOO": ["SPY", "IVV"],
    "QQQ": ["ONEQ", "QQQM"],
    "AAPL": ["MSFT", "GOOGL"],
    "MSFT": ["AAPL", "GOOGL"],
    "GOOGL": ["MSFT", "META"],
    "AMZN": ["MSFT", "GOOGL"],
    "META": ["GOOGL", "SNAP"],
    "TSLA": ["NIO", "RIVN"],
    "BTC-USD": ["ETH-USD", "LTC-USD"],
    "ETH-USD": ["BTC-USD", "SOL-USD"],
}


@dataclass
class HoldingInfo:
    ticker: str
    shares: float
    cost_basis: float  # per share
    purchase_date: date


@dataclass
class TaxLossHarvestSuggestion:
    ticker: str
    current_price: float
    cost_basis: float
    unrealized_loss: float
    loss_pct: float
    action: str
    replacement_tickers: List[str]
    wash_sale_warning: bool


def _get_price(ticker: str) -> float:
    hist = yf.Ticker(ticker).history(period="1d")
    return float(hist["Close"].iloc[-1]) if not hist.empty else 0.0


def analyze_tax_loss_opportunities(
    holdings: List[HoldingInfo],
    min_loss_threshold: float = 100.0,
) -> List[TaxLossHarvestSuggestion]:
    today = date.today()
    suggestions: List[TaxLossHarvestSuggestion] = []

    for h in holdings:
        price = _get_price(h.ticker)
        if price <= 0:
            continue

        unrealized = (price - h.cost_basis) * h.shares
        loss_pct = (price - h.cost_basis) / h.cost_basis * 100 if h.cost_basis > 0 else 0

        if unrealized >= -min_loss_threshold:
            continue

        days_held = (today - h.purchase_date).days
        suggestions.append(
            TaxLossHarvestSuggestion(
                ticker=h.ticker,
                current_price=round(price, 2),
                cost_basis=round(h.cost_basis, 2),
                unrealized_loss=round(unrealized, 2),
                loss_pct=round(loss_pct, 2),
                action="Sell to harvest tax loss, then buy replacement after 30 days",
                replacement_tickers=_SUBSTITUTES.get(h.ticker, []),
                wash_sale_warning=days_held < 30,
            )
        )

    return sorted(suggestions, key=lambda s: s.unrealized_loss)
