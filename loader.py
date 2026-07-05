"""
Handles reading holdings.csv and trades.csv into Pandas DataFrames.

We keep the loaded data in a simple dictionary (`_DATA`) instead of a
class, since a single global cache is all this project needs — two
DataFrames that get replaced whenever a new file is uploaded.
"""

from pathlib import Path
import pandas as pd

from config import HOLDINGS_PATH, TRADES_PATH, HOLDINGS_NUMERIC_COLUMNS, TRADES_NUMERIC_COLUMNS

# Module-level cache. Holds the two DataFrames once loaded, so we don't
# re-read the CSV from disk every time a question is asked.
_DATA: dict[str, pd.DataFrame | None] = {
    "holdings": None,
    "trades": None,
}


def _read_csv(path: Path, numeric_columns: list[str]) -> pd.DataFrame:
    """Read a CSV file and convert the given columns to numbers.

    Any value that can't be converted (blank, text, etc.) becomes NaN
    instead of crashing the whole load — this keeps the app usable even
    with slightly messy real-world data.
    """
    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]  # remove stray spaces

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def load_default_data() -> None:
    """Load the bundled sample CSVs from the data/ folder at startup."""
    if HOLDINGS_PATH.exists():
        _DATA["holdings"] = _read_csv(HOLDINGS_PATH, HOLDINGS_NUMERIC_COLUMNS)

    if TRADES_PATH.exists():
        _DATA["trades"] = _read_csv(TRADES_PATH, TRADES_NUMERIC_COLUMNS)


def load_holdings_file(file_path: str) -> str:
    """Load a new holdings.csv uploaded by the user. Returns a status message."""
    try:
        _DATA["holdings"] = _read_csv(Path(file_path), HOLDINGS_NUMERIC_COLUMNS)
        rows = len(_DATA["holdings"])
        return f"holdings.csv loaded successfully ({rows} rows)"
    except Exception as error:
        return f"Could not load holdings.csv: {error}"


def load_trades_file(file_path: str) -> str:
    """Load a new trades.csv uploaded by the user. Returns a status message."""
    try:
        _DATA["trades"] = _read_csv(Path(file_path), TRADES_NUMERIC_COLUMNS)
        rows = len(_DATA["trades"])
        return f"trades.csv loaded successfully ({rows} rows)"
    except Exception as error:
        return f"Could not load trades.csv: {error}"


def get_holdings() -> pd.DataFrame | None:
    """Return the currently loaded holdings DataFrame, or None if not loaded."""
    return _DATA["holdings"]


def get_trades() -> pd.DataFrame | None:
    """Return the currently loaded trades DataFrame, or None if not loaded."""
    return _DATA["trades"]


def is_data_ready() -> bool:
    """True if at least one dataset has been loaded."""
    return _DATA["holdings"] is not None or _DATA["trades"] is not None


def get_status_text() -> str:
    """A short human-readable status string used by the UI's status bar."""
    holdings_status = "loaded" if _DATA["holdings"] is not None else "not loaded"
    trades_status = "loaded" if _DATA["trades"] is not None else "not loaded"

    holdings_rows = len(_DATA["holdings"]) if _DATA["holdings"] is not None else 0
    trades_rows = len(_DATA["trades"]) if _DATA["trades"] is not None else 0

    return (
        f"holdings.csv: {holdings_status} ({holdings_rows} rows)  |  "
        f"trades.csv: {trades_status} ({trades_rows} rows)"
    )


def get_unique_portfolio_names() -> list[str]:
    """Collect all distinct portfolio names across both datasets.

    Used by classifier.py to fuzzy-match a portfolio name the user typed
    against the real names that actually exist in the data.
    """
    names = set()

    holdings = _DATA["holdings"]
    if holdings is not None and "PortfolioName" in holdings.columns:
        names.update(holdings["PortfolioName"].dropna().unique().tolist())

    trades = _DATA["trades"]
    if trades is not None and "PortfolioName" in trades.columns:
        names.update(trades["PortfolioName"].dropna().unique().tolist())

    return sorted(names)
