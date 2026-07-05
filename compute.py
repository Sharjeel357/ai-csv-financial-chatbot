"""
This is the ONLY file in the whole project that does math.

Every function here takes a Pandas DataFrame and a query plan (the
JSON dictionary produced by classifier.py) and returns a plain
dictionary with the result. Filtering, grouping, sums, averages,
sorting — it all happens here, with plain Pandas — never inside the LLM.
"""

import pandas as pd

from utils import fuzzy_match_name
from loader import get_unique_portfolio_names


def _apply_filters(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    """Narrow a DataFrame down using the portfolio_name / year from the plan.

    If the user typed a slightly wrong portfolio name, we fuzzy-match it
    against the real names in the data before filtering.
    """
    filtered = df.copy()

    portfolio_name = plan.get("portfolio_name")
    if portfolio_name and "PortfolioName" in filtered.columns:
        known_names = get_unique_portfolio_names()
        matched_name = fuzzy_match_name(portfolio_name, known_names)
        if matched_name:
            filtered = filtered[filtered["PortfolioName"] == matched_name]

    year = plan.get("year")
    if year and "Year" in filtered.columns:
        filtered = filtered[filtered["Year"] == year]

    return filtered


def _empty_result(metric: str) -> dict:
    """A standard 'nothing to show' result, used when data is missing."""
    return {"metric": metric, "value": None, "table": None, "row_count": 0}


# ----------------------------------------------------------------------
# Holdings metrics
# ----------------------------------------------------------------------

def total_holdings(df: pd.DataFrame, plan: dict) -> dict:
    """Count how many holding rows match the filters."""
    filtered = _apply_filters(df, plan)
    return {"metric": "total_holdings", "value": len(filtered), "table": None, "row_count": len(filtered)}


def average_holding_price(df: pd.DataFrame, plan: dict) -> dict:
    """Average of the Price column across matching holdings."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "Price" not in filtered.columns:
        return _empty_result("average_holding_price")

    value = round(filtered["Price"].mean(), 2)
    return {"metric": "average_holding_price", "value": value, "table": None, "row_count": len(filtered)}


def total_market_value(df: pd.DataFrame, plan: dict) -> dict:
    """Sum of MV_Base (market value) across matching holdings."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "MV_Base" not in filtered.columns:
        return _empty_result("total_market_value")

    value = round(filtered["MV_Base"].sum(), 2)
    return {"metric": "total_market_value", "value": value, "table": None, "row_count": len(filtered)}


def total_pl_ytd(df: pd.DataFrame, plan: dict) -> dict:
    """Sum of PL_YTD (profit/loss year-to-date) across matching holdings."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "PL_YTD" not in filtered.columns:
        return _empty_result("total_pl_ytd")

    value = round(filtered["PL_YTD"].sum(), 2)
    return {"metric": "total_pl_ytd", "value": value, "table": None, "row_count": len(filtered)}


def best_performing_fund(df: pd.DataFrame, plan: dict) -> dict:
    """Find the single portfolio with the highest total PL_YTD."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "PortfolioName" not in filtered.columns or "PL_YTD" not in filtered.columns:
        return _empty_result("best_performing_fund")

    grouped = filtered.groupby("PortfolioName")["PL_YTD"].sum().sort_values(ascending=False)
    if grouped.empty:
        return _empty_result("best_performing_fund")

    best_name = grouped.index[0]
    best_value = round(grouped.iloc[0], 2)

    table = grouped.reset_index().round(2).to_dict(orient="records")
    return {
        "metric": "best_performing_fund",
        "value": best_value,
        "table": table,
        "row_count": len(filtered),
        "best_portfolio": best_name,
    }


def portfolio_comparison(df: pd.DataFrame, plan: dict) -> dict:
    """Compare all portfolios side by side (market value and PL_YTD)."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "PortfolioName" not in filtered.columns:
        return _empty_result("portfolio_comparison")

    columns_to_sum = [col for col in ["MV_Base", "PL_YTD"] if col in filtered.columns]
    if not columns_to_sum:
        return _empty_result("portfolio_comparison")

    grouped = filtered.groupby("PortfolioName")[columns_to_sum].sum().round(2)
    grouped = grouped.sort_values(by=columns_to_sum[0], ascending=False).reset_index()

    table = grouped.to_dict(orient="records")
    return {"metric": "portfolio_comparison", "value": None, "table": table, "row_count": len(filtered)}


def year_analysis(df: pd.DataFrame, plan: dict) -> dict:
    """Break down PL_YTD (or just row counts) by year."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "Year" not in filtered.columns:
        return _empty_result("year_analysis")

    if "PL_YTD" in filtered.columns:
        grouped = filtered.groupby("Year")["PL_YTD"].sum().round(2).reset_index()
    else:
        grouped = filtered.groupby("Year").size().reset_index(name="count")

    grouped = grouped.sort_values(by="Year")
    table = grouped.to_dict(orient="records")
    return {"metric": "year_analysis", "value": None, "table": table, "row_count": len(filtered)}


def top_portfolios(df: pd.DataFrame, plan: dict, default_n: int = 5) -> dict:
    """Return the N best portfolios ranked by total PL_YTD."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "PortfolioName" not in filtered.columns or "PL_YTD" not in filtered.columns:
        return _empty_result("top_portfolios")

    top_n = plan.get("top_n") or default_n
    grouped = filtered.groupby("PortfolioName")["PL_YTD"].sum().sort_values(ascending=False)
    top_rows = grouped.head(top_n).round(2).reset_index()

    table = top_rows.to_dict(orient="records")
    return {"metric": "top_portfolios", "value": None, "table": table, "row_count": len(filtered)}


def bottom_portfolios(df: pd.DataFrame, plan: dict, default_n: int = 5) -> dict:
    """Return the N worst portfolios ranked by total PL_YTD."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "PortfolioName" not in filtered.columns or "PL_YTD" not in filtered.columns:
        return _empty_result("bottom_portfolios")

    bottom_n = plan.get("top_n") or default_n
    grouped = filtered.groupby("PortfolioName")["PL_YTD"].sum().sort_values(ascending=True)
    bottom_rows = grouped.head(bottom_n).round(2).reset_index()

    table = bottom_rows.to_dict(orient="records")
    return {"metric": "bottom_portfolios", "value": None, "table": table, "row_count": len(filtered)}


# ----------------------------------------------------------------------
# Trades metrics
# ----------------------------------------------------------------------

def total_trades(df: pd.DataFrame, plan: dict) -> dict:
    """Count how many trade rows match the filters."""
    filtered = _apply_filters(df, plan)
    return {"metric": "total_trades", "value": len(filtered), "table": None, "row_count": len(filtered)}


def average_trade_price(df: pd.DataFrame, plan: dict) -> dict:
    """Average of the Price column across matching trades."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "Price" not in filtered.columns:
        return _empty_result("average_trade_price")

    value = round(filtered["Price"].mean(), 2)
    return {"metric": "average_trade_price", "value": value, "table": None, "row_count": len(filtered)}


def total_traded_cash(df: pd.DataFrame, plan: dict) -> dict:
    """Sum of TotalCash across matching trades."""
    filtered = _apply_filters(df, plan)
    if filtered.empty or "TotalCash" not in filtered.columns:
        return _empty_result("total_traded_cash")

    value = round(filtered["TotalCash"].sum(), 2)
    return {"metric": "total_traded_cash", "value": value, "table": None, "row_count": len(filtered)}


def trade_profit_guard(df: pd.DataFrame, plan: dict) -> dict:
    """Guarded metric — trades.csv has no profit/loss column.

    Instead of guessing a number, we return a clear explanation. This
    is the guardrail in action: better to say "I can't calculate this"
    than to make up a figure.
    """
    row_count = len(df) if df is not None else 0
    return {
        "metric": "trade_profit",
        "value": None,
        "table": None,
        "row_count": row_count,
        "is_guarded": True,
        "guard_message": (
            "trades.csv only records transaction details (quantity, price, cash) "
            "and does not include a cost-basis or realized profit/loss column. "
            "Trade-level profit cannot be calculated from this dataset. "
            "For profit and loss figures, ask about holdings instead (PL_YTD)."
        ),
    }


# ----------------------------------------------------------------------
# Dispatch table — maps a metric name to the function that computes it.
# This replaces a long if/elif chain with a simple dictionary lookup.
# ----------------------------------------------------------------------
METRIC_FUNCTIONS = {
    "total_holdings": total_holdings,
    "average_holding_price": average_holding_price,
    "total_market_value": total_market_value,
    "total_pl_ytd": total_pl_ytd,
    "best_performing_fund": best_performing_fund,
    "portfolio_comparison": portfolio_comparison,
    "year_analysis": year_analysis,
    "top_portfolios": top_portfolios,
    "bottom_portfolios": bottom_portfolios,
    "total_trades": total_trades,
    "average_trade_price": average_trade_price,
    "total_traded_cash": total_traded_cash,
    "trade_profit": trade_profit_guard,
}

# Metrics that must always run against holdings.csv, no matter what the
# LLM chose — this is a safety net against the LLM picking the wrong file.
HOLDINGS_ONLY_METRICS = {
    "total_holdings", "average_holding_price", "total_market_value",
    "total_pl_ytd", "best_performing_fund", "portfolio_comparison",
    "top_portfolios", "bottom_portfolios",
}

# Metrics that must always run against trades.csv.
TRADES_ONLY_METRICS = {
    "total_trades", "average_trade_price", "total_traded_cash", "trade_profit",
}


def run_query(holdings_df: pd.DataFrame | None, trades_df: pd.DataFrame | None, plan: dict) -> dict:
    """Run the correct compute function for this plan and return the result.

    This function decides the FINAL dataset to use — overriding the
    LLM's choice if the metric only makes sense for one dataset. That
    way, even if the LLM gets confused, the numbers still come from the
    right place.
    """
    metric = plan.get("metric", "total_holdings")
    compute_function = METRIC_FUNCTIONS.get(metric, total_holdings)

    if metric in HOLDINGS_ONLY_METRICS:
        dataset = holdings_df
    elif metric in TRADES_ONLY_METRICS:
        dataset = trades_df
    else:
        dataset = holdings_df if plan.get("dataset") == "holdings" else trades_df

    if dataset is None:
        return _empty_result(metric)

    return compute_function(dataset, plan)
