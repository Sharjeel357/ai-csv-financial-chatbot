# AI-Powered CSV Financial Chatbot for Real-Estate Portfolio Analysis

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/b0e9d749-2773-43e4-a1ed-c01bd27886a6" />


An AI-powered chatbot that answers financial questions from **two CSV files** using **Python, Pandas, Groq LLM, and Gradio**.

Instead of manually searching through large CSV files, users can ask questions in simple English, and the chatbot analyzes the data to provide accurate answers.

---

## Features

- Natural language financial queries
- Works with **holdings.csv** and **trades.csv**
- Accurate calculations using **Pandas**
- Groq LLM for query understanding
- Interactive Gradio interface
- Portfolio comparison
- Year-wise analysis
- Automatic charts
- Simple and beginner-friendly architecture

---

## Tech Stack

- Python
- Pandas
- NumPy
- Groq API
- Gradio
- Plotly
- RapidFuzz

---

# Project Architecture

```text
            User Question
                  │
                  ▼
           Rule Engine
                  │
                  ▼
      Groq Query Classifier
                  │
                  ▼
            JSON Query Plan
                  │
                  ▼
      Pandas Compute Engine
                  │
                  ▼
     Groq Answer Generator
                  │
                  ▼
           Final Response
```

---

## How It Works

### Rule Engine
Checks the user's question and decides which CSV file should be used.

### Groq Query Classifier
Uses the Groq LLM to understand the user's question and convert it into a structured query plan.

### Pandas Compute Engine
Performs all calculations including:

- Filtering
- Grouping
- Sum
- Average
- Count
- Maximum
- Minimum
- Portfolio comparison

### Groq Answer Generator
Converts the calculated result into a simple and human-readable answer.

> **Note:** The LLM never performs calculations. All mathematical operations are handled by Pandas.

---

## Folder Structure

```text
project/
│
├── app.py
├── config.py
├── loader.py
├── classifier.py
├── rules.py
├── compute.py
├── answer.py
├── charts.py
├── utils.py
├── tests.py
│
├── requirements.txt
├── README.md
├── .env.example
│
├── data/
│   ├── holdings.csv
│   └── trades.csv
│
└── assets/
```

---

## Installation

Clone the repository

```bash
git clone https://github.com/Sharjeel357/ai-csv-financial-chatbot.git
cd ai-csv-financial-chatbot
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file and add your Groq API key.

Run the application

```bash
python app.py
```

Open the Gradio URL shown in your terminal.

---

## Example Questions

- How many holdings are there?
- How many trades were executed?
- What is the total market value?
- What is the average holding price?
- What is the average trade price?
- Which portfolio performed the best?
- Compare portfolios by market value.
- Show year-wise performance.
- Show the top 5 portfolios.
- Show the bottom 5 portfolios.

---

## Sample Screenshots

### Dashboard

```
assets/dashboard.png
```

### Chat Interface

```
assets/chat.png
```

### Charts

```
assets/chart.png
```

### Data Preview

```
assets/data-preview.png
```

---

## Why I Built This Project

The goal of this project was to create a simple AI application that combines **Natural Language Processing** with **financial data analysis**.

Instead of using complex frameworks like LangChain or vector databases, I used **Pandas** for all calculations because the data is already stored in structured CSV files.

This keeps the project:

- Simple
- Easy to understand
- Easy to explain
- Beginner friendly
- Accurate for financial calculations

---

## Future Improvements

- Upload custom CSV files
- More financial metrics
- Better visualizations
- Export reports as PDF or Excel
- Voice-based interaction
- Online deployment

---

## License

This project is developed for learning and educational purposes.

MIT License.
