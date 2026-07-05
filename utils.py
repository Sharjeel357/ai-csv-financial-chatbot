"""
Small helper functions used in more than one place. Nothing here is
specific to any one pipeline stage — just generic formatting and
fuzzy-matching helpers.
"""

from datetime import datetime
from rapidfuzz import process, fuzz

from config import FUZZY_MATCH_THRESHOLD


def format_currency(value: float | None) -> str:
    """Format a number as currency, e.g. 1234.5 -> '$1,234.50'."""
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


def format_number(value: float | None) -> str:
    """Format a plain number with thousands separators, e.g. 1234 -> '1,234'."""
    if value is None:
        return "N/A"
    return f"{value:,.2f}"


def format_count(value: float | None) -> str:
    """Format a count as a whole number, e.g. 1234.0 -> '1,234'."""
    if value is None:
        return "N/A"
    return f"{int(value):,}"


def timestamp() -> str:
    """Current date/time as a readable string, used for chat exports."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fuzzy_match_name(name: str, known_names: list[str]) -> str | None:
    """Find the closest match for `name` inside `known_names`.

    This is used to correct small typos in portfolio names. For example,
    if the user (or the LLM) types "alpha real estate" but the real name
    in the CSV is "Alpha Real Estate Fund", this returns the correct one.

    Returns None if nothing is a close enough match.
    """
    if not name or not known_names:
        return None

    result = process.extractOne(name, known_names, scorer=fuzz.WRatio)
    if result is None:
        return None

    best_match, score, _ = result
    if score >= FUZZY_MATCH_THRESHOLD:
        return best_match

    return None
