"""
The Rule Engine — a simple, fast, keyword-based first pass that runs
BEFORE the question reaches the LLM.

It does two jobs:
  1. Guess whether the question is about holdings.csv or trades.csv,
     just by looking for obvious keywords. This gets passed to the LLM
     as a hint, so it doesn't have to guess from scratch.
  2. Catch questions that can NEVER be answered honestly — right now,
     that's asking for "trade profit". trades.csv only has transaction
     details (quantity, price, cash); it has no profit/loss column.
     Without this check, the LLM might try to invent a number for it.
"""

HOLDINGS_KEYWORDS = [
    "holding", "holdings", "performance", "p&l", "pl", "profit and loss",
    "market value", "price", "position", "best performing", "worst performing",
    "ytd", "mtd", "qtd", "dtd",
]

TRADES_KEYWORDS = [
    "trade", "trades", "transaction", "cash", "volume", "buy", "sell", "traded",
]

# Phrases that specifically mean "profit made on a trade" — this is the
# one thing our data genuinely cannot answer.
TRADE_PROFIT_PHRASES = [
    "trade profit", "profit on trade", "trades profit", "trading profit",
    "profit from trade", "trade pnl", "trade p&l",
]


def check_trade_profit_guard(question: str) -> bool:
    """Return True if the question is asking for trade-level profit.

    This is the guardrail that prevents hallucination: trades.csv has
    no cost-basis or profit column, so this kind of question must be
    answered with an honest explanation instead of a made-up number.

    We check for an exact phrase match first (fast, precise), then fall
    back to "does the question mention both profit and trade, without
    also mentioning holdings" — since real questions are rarely worded
    exactly like our phrase list (e.g. "profit on our trades").
    """
    question_lower = question.lower()

    if any(phrase in question_lower for phrase in TRADE_PROFIT_PHRASES):
        return True

    mentions_profit = any(word in question_lower for word in ["profit", "pnl", "p&l", "gain"])
    mentions_trade = any(word in question_lower for word in ["trade", "trades", "trading"])
    mentions_holdings = any(word in question_lower for word in ["holding", "holdings", "position"])

    return mentions_profit and mentions_trade and not mentions_holdings


def guess_dataset(question: str) -> str:
    """Guess which dataset ('holdings' or 'trades') the question is about.

    This is only a HINT for the LLM — the LLM can still override it if
    the question is more nuanced. It's just here to make the LLM's job
    easier and cheaper (less guessing = more consistent results).
    """
    question_lower = question.lower()

    holdings_hits = sum(1 for word in HOLDINGS_KEYWORDS if word in question_lower)
    trades_hits = sum(1 for word in TRADES_KEYWORDS if word in question_lower)

    if trades_hits > holdings_hits:
        return "trades"
    return "holdings"  # default to holdings when unclear or tied


def apply_rules(question: str) -> dict:
    """Run the rule engine on a question and return a small hint dictionary.

    Example return value:
        {"likely_dataset": "holdings", "is_guarded": False}
    """
    if check_trade_profit_guard(question):
        return {"likely_dataset": "trades", "is_guarded": True}

    return {"likely_dataset": guess_dataset(question), "is_guarded": False}
