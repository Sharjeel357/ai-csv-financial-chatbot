"""
All the settings for this project live here — API keys, file paths,
and small lists of constants (column names, sample questions, etc.).

Keeping configuration in one place means if you ever need to change a
folder path or add a new sample question, you only edit this file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from a .env file (if one exists) into the environment.
# This lets you keep your GROQ_API_KEY out of the source code.
load_dotenv()

# --------------------------------------------------------------------
# Groq LLM settings
# --------------------------------------------------------------------
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TEMPERATURE: float = 0.2
GROQ_MAX_TOKENS: int = 800

# --------------------------------------------------------------------
# File paths
# --------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"

HOLDINGS_PATH: Path = DATA_DIR / "holdings.csv"
TRADES_PATH: Path = DATA_DIR / "trades.csv"

# --------------------------------------------------------------------
# Gradio app settings
# --------------------------------------------------------------------
APP_TITLE: str = "Real Estate Portfolio Chatbot"
SERVER_NAME: str = "127.0.0.1"
SERVER_PORT: int = 7860

# --------------------------------------------------------------------
# Holdings.csv columns we actually use
# --------------------------------------------------------------------
HOLDINGS_NUMERIC_COLUMNS = [
    "Qty", "Price", "MV_Base", "PL_DTD", "PL_QTD", "PL_MTD", "PL_YTD", "Year",
]

# --------------------------------------------------------------------
# Trades.csv columns we actually use
# --------------------------------------------------------------------
TRADES_NUMERIC_COLUMNS = [
    "Quantity", "Price", "TotalCash", "Year",
]

# --------------------------------------------------------------------
# Sample questions shown as quick-click buttons in the sidebar
# --------------------------------------------------------------------
SAMPLE_QUESTIONS = [
    "How many holdings do we have?",
    "How many trades were executed?",
    "What is the average holding price?",
    "What is the average trade price?",
    "Which fund is performing the best?",
    "What is the total PL_YTD?",
    "What is the total traded cash?",
    "What is the total market value?",
    "Compare portfolios by market value",
    "Show year-wise performance",
    "Show the top 5 portfolios",
    "Show the bottom 5 portfolios",
]

# Threshold (0-100) for fuzzy-matching portfolio names typed by the user.
FUZZY_MATCH_THRESHOLD: int = 70
