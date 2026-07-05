#  AI-Powered CSV Financial Chatbot — Real-Estate Portfolio Analysis

A chatbot that answers plain-English questions about real-estate investment
data — directly from two CSV files. Built with Python, Pandas, the Groq LLM
API, and Gradio. No database, no SQL, no LangChain, no vector search — just
a clean, understandable pipeline that a single developer can read start to
finish.

---

##  Project Overview

You give it two CSV files:
- **holdings.csv** — one row per investment position (price, quantity,
  market value, profit/loss)
- **trades.csv** — one row per transaction (quantity, price, cash)

You ask questions like *"What is the total market value?"* or *"Which
fund is performing the best?"* and it gives you a real, calculated
answer — with an optional chart.

**The core idea:** the AI (Groq) never does math. It only (1) figures out
*what* to calculate, and (2) explains a number that was already calculated
by Pandas. This means the chatbot can never "hallucinate" a financial
figure — every number comes from a plain, testable line of Pandas code.

---

##  Architecture

```
User Question
     |
     v
Rule Engine            (rules.py)        -- keyword hints + guardrail
     |
     v
Groq Query Classifier  (classifier.py)   -- LLM turns question into JSON plan
     |
     v
Query Plan             (a small dict)     -- e.g. {"metric": "total_pl_ytd", ...}
     |
     v
Pandas Compute Engine  (compute.py)      -- ALL the math happens here
     |
     v
Groq Answer Generator  (answer.py)       -- LLM explains the calculated number
     |
     v
Response (+ optional chart)
```

**Why split it this way?** Each stage has one job. The LLM stages
(classifier.py, answer.py) never touch a number. The math stage
(compute.py) never talks to the LLM. If something's wrong with an
answer, you know exactly which file to check.

---

##  Folder Structure

```
project/
├── app.py              # Entry point — Gradio UI + pipeline orchestration
├── config.py           # Settings: API key, file paths, sample questions
├── loader.py            # Reads holdings.csv / trades.csv into DataFrames
├── rules.py              # Rule engine — keyword hints + guardrail
├── classifier.py          # Groq call #1 — question -> JSON query plan
├── compute.py              # Pandas calculations — the only file that does math
├── answer.py                # Groq call #2 — explains the calculated result
├── charts.py                 # Builds a Plotly chart from a result
├── utils.py                   # Formatting helpers + fuzzy name matching
├── tests.py                    # Simple sanity checks (no pytest needed)
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
│   ├── holdings.csv            # Sample dataset (400 rows)
│   └── trades.csv               # Sample dataset (500 rows)
└── assets/                       # Screenshots for this README
```

That's **9 Python files** doing all the work, plus one simple test file.

---

##  Installation

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/ai-csv-financial-chatbot.git
cd ai-csv-financial-chatbot

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Groq API key
cp .env.example .env
# open .env and paste your key (free at https://console.groq.com)

# 5. Run it
python app.py
```

Open the URL printed in your terminal (usually `http://127.0.0.1:7860`).
The sample `data/holdings.csv` and `data/trades.csv` load automatically.

> **No Groq key?** The app still works — it falls back to simple keyword
> matching for both understanding your question and explaining the
> answer. You lose some conversational flexibility, not functionality.

---

##  Screenshots

*(Run the app and place your own screenshots in `assets/`, then they'll
show up here.)*

| Dashboard | Chat Example |
|---|---|
| `assets/dashboard.png` | `assets/chat-example.png` |

| Chart Example | Data Preview |
|---|---|
| `assets/chart-example.png` | `assets/data-preview.png` |

---

##  How It Works

1. **You type a question** in the chat box.
2. **Rule Engine (`rules.py`)** does a quick keyword scan — is this about
   holdings or trades? Is it asking for something we genuinely can't
   calculate (like trade-level profit)?
3. **Groq Query Classifier (`classifier.py`)** sends your question to the
   Groq LLM with strict instructions: "don't answer, just tell me what to
   calculate." The LLM replies with a small JSON plan like:
   ```json
   {"dataset": "holdings", "metric": "total_pl_ytd", "portfolio_name": null, "year": 2025, "top_n": null}
   ```
4. **Pandas Compute Engine (`compute.py`)** reads that plan and runs the
   actual calculation — filtering, grouping, summing, averaging, or
   sorting the DataFrame. This is the only place numbers are produced.
5. **Groq Answer Generator (`answer.py`)** takes the calculated number and
   turns it into a friendly sentence — again, without being allowed to
   change the number.
6. **Charts (`charts.py`)** builds a bar chart automatically if the result
   has a breakdown (like a portfolio comparison).
7. The final answer and chart appear in the chat window.

### The guardrail, explained simply

`trades.csv` doesn't have a profit/loss column — only price, quantity,
and cash. If you ask *"what's the profit on our trades?"*, the rule engine
catches this **before** the question even reaches the LLM, and returns an
honest explanation instead of letting the AI guess a number.

---

##  Example Queries

- "How many holdings do we have?"
- "How many trades were executed?"
- "What is the average holding price?"
- "What is the average trade price?"
- "Which fund is performing the best?"
- "What is the total PL_YTD?"
- "What is the total traded cash?"
- "What is the total market value?"
- "Compare portfolios by market value"
- "Show year-wise performance"
- "Show the top 5 portfolios"
- "Show the bottom 5 portfolios"
- "What is the profit on our trades?" *(guarded — explains why it can't answer)*

---

##  Testing

```bash
python tests.py
```

This runs a handful of plain `assert`-based checks on the rule engine's
guardrail and the compute engine's math — no pytest installation needed.
You should see `All tests passed!` at the end.

---

##  Future Improvements

- Add more metrics (e.g. quarter-over-quarter comparison)
- Support additional file uploads beyond the two default CSVs
- Cache repeated questions so identical queries don't re-call the LLM
- Add simple user authentication if this ever needs to be shared
- Package as a downloadable desktop app with PyInstaller
- Add more chart types (pie chart for portfolio allocation, line chart
  for year-over-year trend)

---

##  Why This Design?

This project intentionally avoids heavier tools like LangChain, RAG,
vector databases, or a backend framework. For a two-CSV question-
answering tool, those add complexity without adding value — the data
easily fits in memory, and Pandas already does everything needed for
filtering and aggregation. Keeping the architecture simple made every
part of it easy to build, test, and explain.

---

##  License

MIT — free to use, modify, and learn from.
