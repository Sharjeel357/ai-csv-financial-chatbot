"""
A few simple sanity checks for the most important logic in this
project — the rule engine's guardrail, and the compute engine's math.

This intentionally does NOT use pytest, to keep the dependency list
small. Run it directly with:

    python tests.py

If everything passes, you'll see "All tests passed!" at the end.
"""

import pandas as pd

from rules import apply_rules, check_trade_profit_guard
from compute import total_holdings, average_holding_price, total_pl_ytd, run_query


def test_trade_profit_guard_catches_the_right_questions():
    assert check_trade_profit_guard("What is the profit on our trades?") is True
    assert check_trade_profit_guard("What's our trading profit?") is True
    assert check_trade_profit_guard("What is the total PL_YTD?") is False
    assert check_trade_profit_guard("How many holdings do we have?") is False
    print("PASS: trade profit guard catches the right questions")


def test_apply_rules_returns_guard_flag():
    hint = apply_rules("What is the profit on our trades?")
    assert hint["is_guarded"] is True

    hint = apply_rules("What is the average holding price?")
    assert hint["is_guarded"] is False
    print("PASS: apply_rules sets the guard flag correctly")


def _sample_holdings() -> pd.DataFrame:
    """A tiny, hand-built DataFrame so tests don't depend on data/holdings.csv."""
    return pd.DataFrame({
        "PortfolioName": ["Alpha", "Alpha", "Beta"],
        "Price": [100.0, 200.0, 300.0],
        "MV_Base": [1000.0, 2000.0, 3000.0],
        "PL_YTD": [10.0, -5.0, 20.0],
        "Year": [2024, 2024, 2025],
    })


def test_total_holdings_counts_rows():
    df = _sample_holdings()
    result = total_holdings(df, {})
    assert result["value"] == 3
    print("PASS: total_holdings counts rows correctly")


def test_average_holding_price_is_correct():
    df = _sample_holdings()
    result = average_holding_price(df, {})
    assert result["value"] == 200.0  # (100 + 200 + 300) / 3
    print("PASS: average_holding_price calculates the correct average")


def test_total_pl_ytd_sums_correctly():
    df = _sample_holdings()
    result = total_pl_ytd(df, {})
    assert result["value"] == 25.0  # 10 - 5 + 20
    print("PASS: total_pl_ytd sums PL_YTD correctly")


def test_run_query_forces_correct_dataset():
    """Even if the plan says 'trades', a holdings-only metric should
    still be computed on the holdings DataFrame — this is the safety
    net described in compute.py's HOLDINGS_ONLY_METRICS set."""
    holdings_df = _sample_holdings()
    trades_df = pd.DataFrame({"PortfolioName": ["Gamma"], "Price": [999.0]})

    plan = {"dataset": "trades", "metric": "total_pl_ytd", "portfolio_name": None, "year": None, "top_n": None}
    result = run_query(holdings_df, trades_df, plan)

    assert result["value"] == 25.0  # came from holdings_df, not trades_df
    print("PASS: run_query forces the correct dataset regardless of the LLM's choice")


if __name__ == "__main__":
    test_trade_profit_guard_catches_the_right_questions()
    test_apply_rules_returns_guard_flag()
    test_total_holdings_counts_rows()
    test_average_holding_price_is_correct()
    test_total_pl_ytd_sums_correctly()
    test_run_query_forces_correct_dataset()
    print("\nAll tests passed!")
