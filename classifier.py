"""
This is where the LLM is used for the FIRST time: turning a natural
language question into a small JSON "execution plan".

IMPORTANT: the LLM never calculates anything here. It only decides
WHAT should be calculated (which dataset, which metric, which filters).
The actual math happens later, in compute.py, using Pandas.

If the Groq API is not available (no API key, network error, bad
response), we fall back to a simple keyword-based planner so the app
still works without an LLM.
"""

import json
import re
from typing import Any

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS

# The list of metrics our compute engine knows how to calculate.
# Keeping this list here (and in the prompt below) stops the LLM from
# inventing metric names we don't support.
SUPPORTED_METRICS = [
    "total_holdings",
    "total_trades",
    "average_holding_price",
    "average_trade_price",
    "best_performing_fund",
    "total_pl_ytd",
    "total_traded_cash",
    "total_market_value",
    "portfolio_comparison",
    "year_analysis",
    "top_portfolios",
    "bottom_portfolios",
    "trade_profit",  # guarded: trades.csv has no profit column
]

PLANNER_SYSTEM_PROMPT = f"""You are a query planner for a real-estate portfolio chatbot.
You do NOT answer questions and you do NOT calculate anything.
Your only job is to read the user's question and output a small JSON plan
describing what to calculate.

There are two datasets:
- "holdings": one row per investment position. Has PortfolioName, Price, Qty,
  MV_Base (market value), PL_YTD/PL_QTD/PL_MTD/PL_DTD (profit and loss), Year.
- "trades": one row per transaction. Has PortfolioName, Quantity, Price,
  TotalCash, Year. It has NO profit/loss column.

Choose "metric" from exactly this list: {SUPPORTED_METRICS}

If the user asks about profit made on TRADES specifically, use metric
"trade_profit" — do not guess a number, our system will explain why this
cannot be computed from trades.csv.

Respond with ONLY a JSON object, nothing else, in this exact shape:
{{
  "dataset": "holdings" or "trades",
  "metric": "<one of the supported metrics>",
  "portfolio_name": "<portfolio name if mentioned, else null>",
  "year": <year as a number if mentioned, else null>,
  "top_n": <number if the question mentions "top N" or "bottom N", else null>
}}
"""


def _extract_json(text: str) -> dict:
    """Pull the first {...} JSON object out of the LLM's reply.

    LLMs sometimes wrap JSON in markdown code fences or add a sentence
    before/after it, so we search for the object instead of assuming
    the whole reply is clean JSON.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in the LLM's response")
    return json.loads(match.group(0))


def _call_groq_for_plan(question: str, hint: dict) -> dict:
    """Ask Groq to turn the question into a JSON plan."""
    client = Groq(api_key=GROQ_API_KEY)

    user_message = (
        f'User question: "{question}"\n'
        f"Rule engine hint (advisory, you may override): {hint}\n"
        f"Return the JSON plan now."
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=GROQ_TEMPERATURE,
        max_tokens=GROQ_MAX_TOKENS,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    reply_text = response.choices[0].message.content or ""
    return _extract_json(reply_text)


def _keyword_fallback_plan(question: str, hint: dict) -> dict:
    """Build a plan using simple keyword matching, no LLM required.

    This keeps the app fully functional even without a Groq API key —
    just with less flexibility in understanding phrasing.
    """
    question_lower = question.lower()
    dataset = hint.get("likely_dataset", "holdings")

    if hint.get("is_guarded"):
        metric = "trade_profit"
        dataset = "trades"
    elif "average" in question_lower and "trade" in question_lower:
        metric, dataset = "average_trade_price", "trades"
    elif "average" in question_lower:
        metric, dataset = "average_holding_price", "holdings"
    elif "best" in question_lower or "top" in question_lower:
        metric, dataset = ("top_portfolios", "holdings") if "top" in question_lower else ("best_performing_fund", "holdings")
    elif "bottom" in question_lower or "worst" in question_lower:
        metric, dataset = "bottom_portfolios", "holdings"
    elif "compare" in question_lower:
        metric, dataset = "portfolio_comparison", "holdings"
    elif "year" in question_lower:
        metric, dataset = "year_analysis", "holdings"
    elif "market value" in question_lower:
        metric, dataset = "total_market_value", "holdings"
    elif "pl_ytd" in question_lower or "profit" in question_lower or "ytd" in question_lower:
        metric, dataset = "total_pl_ytd", "holdings"
    elif "cash" in question_lower:
        metric, dataset = "total_traded_cash", "trades"
    elif "how many" in question_lower and "trade" in question_lower:
        metric, dataset = "total_trades", "trades"
    elif "how many" in question_lower and "holding" in question_lower:
        metric, dataset = "total_holdings", "holdings"
    elif "trade" in question_lower:
        metric, dataset = "total_trades", "trades"
    else:
        metric, dataset = "total_holdings", "holdings"

    year_match = re.search(r"\b(20\d{2})\b", question)
    top_n_match = re.search(r"\b(top|bottom)\s+(\d+)\b", question_lower)

    return {
        "dataset": dataset,
        "metric": metric,
        "portfolio_name": None,
        "year": int(year_match.group(1)) if year_match else None,
        "top_n": int(top_n_match.group(2)) if top_n_match else None,
    }


def _validate_plan(plan: dict) -> dict:
    """Make sure the plan has all expected keys and a valid metric name.

    If the LLM returns something malformed or an unknown metric, we
    default to a safe, always-answerable metric instead of crashing.
    """
    plan.setdefault("dataset", "holdings")
    plan.setdefault("portfolio_name", None)
    plan.setdefault("year", None)
    plan.setdefault("top_n", None)

    if plan.get("metric") not in SUPPORTED_METRICS:
        plan["metric"] = "total_holdings"

    return plan


def get_query_plan(question: str, hint: dict) -> dict[str, Any]:
    """Main entry point: turn a question into a validated JSON plan.

    Tries Groq first. Falls back to keyword matching if Groq is not
    configured or the call fails for any reason.
    """
    if GROQ_API_KEY:
        try:
            plan = _call_groq_for_plan(question, hint)
            return _validate_plan(plan)
        except Exception:
            pass  # fall through to the keyword-based backup planner

    plan = _keyword_fallback_plan(question, hint)
    return _validate_plan(plan)
