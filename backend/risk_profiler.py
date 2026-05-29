from dataclasses import dataclass
from typing import Dict, List

RISK_QUESTIONS = [
    {
        "id": "age",
        "question": "What is your age group?",
        "options": [
            {"label": "Under 30", "value": 5},
            {"label": "30-45", "value": 4},
            {"label": "45-60", "value": 2},
            {"label": "Over 60", "value": 1},
        ],
    },
    {
        "id": "horizon",
        "question": "What is your investment time horizon?",
        "options": [
            {"label": "Less than 1 year", "value": 1},
            {"label": "1-3 years", "value": 2},
            {"label": "3-10 years", "value": 4},
            {"label": "More than 10 years", "value": 5},
        ],
    },
    {
        "id": "reaction",
        "question": "If your portfolio dropped 20% in a month, you would:",
        "options": [
            {"label": "Sell everything immediately", "value": 1},
            {"label": "Sell some to reduce risk", "value": 2},
            {"label": "Hold and wait", "value": 4},
            {"label": "Buy more at lower prices", "value": 5},
        ],
    },
    {
        "id": "income",
        "question": "How stable is your primary income?",
        "options": [
            {"label": "Very unstable / freelance", "value": 1},
            {"label": "Somewhat stable", "value": 3},
            {"label": "Very stable (salaried)", "value": 5},
        ],
    },
    {
        "id": "goal",
        "question": "What is your primary investment goal?",
        "options": [
            {"label": "Capital preservation", "value": 1},
            {"label": "Balanced growth and income", "value": 3},
            {"label": "Maximum long-term growth", "value": 5},
        ],
    },
]

_MAX_SCORE = sum(max(o["value"] for o in q["options"]) for q in RISK_QUESTIONS)


@dataclass
class RiskProfile:
    score: int
    category: str
    description: str
    suggested_allocation: Dict[str, float]


def calculate_risk_profile(answers: Dict[str, int]) -> RiskProfile:
    score = sum(answers.values())
    pct = score / _MAX_SCORE

    if pct < 0.4:
        category = "conservative"
        description = (
            "You prioritize capital preservation. "
            "Expect lower but steadier returns with minimal volatility."
        )
        allocation = {
            "US Bonds": 50,
            "International Bonds": 20,
            "US Stocks": 20,
            "International Stocks": 10,
        }
    elif pct < 0.7:
        category = "moderate"
        description = "You seek balanced growth with manageable risk."
        allocation = {
            "US Stocks": 40,
            "International Stocks": 20,
            "US Bonds": 25,
            "International Bonds": 10,
            "Alternatives": 5,
        }
    else:
        category = "aggressive"
        description = (
            "You pursue maximum long-term growth "
            "and can tolerate significant short-term volatility."
        )
        allocation = {
            "US Stocks": 50,
            "International Stocks": 25,
            "Emerging Markets": 15,
            "Alternatives": 10,
        }

    return RiskProfile(
        score=score,
        category=category,
        description=description,
        suggested_allocation=allocation,
    )
