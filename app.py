"""
app.py

The entry point for the whole project. Run this file to start the chatbot:

    python app.py

This file does two things:
  1. Defines `answer_question()` — the function that runs a question
     through the full pipeline (rules -> classifier -> compute -> answer).
  2. Builds and launches the Gradio dashboard (chat window, sidebar,
     charts, data preview) and wires it up to that pipeline function.
"""

import json
from pathlib import Path

import gradio as gr

import config
import loader
import rules
import classifier
import compute
import answer
import charts
from utils import timestamp

# Keeps every question/answer pair asked this session, so "Export Chat"
# has something to write to a file. A simple list is enough here — we
# don't need a database for a single-user local app.
chat_log: list[dict] = []


# ------------------------------------------------------------------------
# The pipeline: one question in, one answer out
# ------------------------------------------------------------------------

def answer_question(question: str):
    """Run the full pipeline for a single question.

    Pipeline steps:
        1. rules.py       -> quick keyword hint + hallucination guard
        2. classifier.py  -> Groq turns the question into a JSON plan
        3. compute.py     -> Pandas performs the actual calculation
        4. answer.py      -> Groq explains the calculated result
        5. charts.py      -> optional chart for the result

    Returns a tuple of (answer_text, chart_or_none).
    """
    question = question.strip()
    if not question:
        return "Please type a question.", None

    if not loader.is_data_ready():
        return "No data is loaded yet. Please upload holdings.csv and/or trades.csv.", None

    # Step 1: Rule Engine
    hint = rules.apply_rules(question)

    # If the rule engine already knows this question can't be answered
    # honestly (e.g. trade profit), skip the LLM entirely and explain why.
    if hint["is_guarded"]:
        result = compute.trade_profit_guard(loader.get_trades(), {})
        answer_text = answer.generate_answer(question, result)
        return answer_text, None

    # Step 2: Groq Query Classifier -> JSON Query Plan
    plan = classifier.get_query_plan(question, hint)

    # Step 3: Pandas Compute Engine
    holdings_df = loader.get_holdings()
    trades_df = loader.get_trades()
    result = compute.run_query(holdings_df, trades_df, plan)

    # Step 4: Groq Answer Generator
    answer_text = answer.generate_answer(question, result)

    # Step 5: Optional chart
    chart_figure = charts.build_chart(result)

    return answer_text, chart_figure


# ------------------------------------------------------------------------
# Gradio UI helper functions
# ------------------------------------------------------------------------

def handle_holdings_upload(file_obj) -> tuple[str, "gr.Dataframe"]:
    """Called when the user uploads a new holdings.csv from the sidebar."""
    if file_obj is None:
        return loader.get_status_text(), _preview("holdings")

    loader.load_holdings_file(file_obj.name)
    return loader.get_status_text(), _preview("holdings")


def handle_trades_upload(file_obj) -> tuple[str, "gr.Dataframe"]:
    """Called when the user uploads a new trades.csv from the sidebar."""
    if file_obj is None:
        return loader.get_status_text(), _preview("trades")

    loader.load_trades_file(file_obj.name)
    return loader.get_status_text(), _preview("trades")


def _preview(name: str):
    """Return the first 50 rows of a dataset for the data preview tab."""
    df = loader.get_holdings() if name == "holdings" else loader.get_trades()
    if df is None:
        import pandas as pd
        return pd.DataFrame({"message": [f"{name}.csv not loaded yet"]})
    return df.head(50)


def handle_chat(question: str, history: list):
    """Called when the user sends a message in the chat window."""
    answer_text, chart_figure = answer_question(question)

    history = history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer_text},
    ]
    chat_log.append({"question": question, "answer": answer_text, "time": timestamp()})

    history_text = _format_history()
    return history, "", chart_figure, history_text


def _format_history() -> str:
    """A short markdown list of past questions, shown in the sidebar."""
    if not chat_log:
        return "_No questions yet._"

    lines = [f"- {entry['question']}" for entry in reversed(chat_log[-10:])]
    return "\n".join(lines)


def handle_clear_chat():
    """Called when the user clicks 'Clear Chat'."""
    chat_log.clear()
    return [], None, "_No questions yet._"


def handle_export_chat():
    """Called when the user clicks 'Export Chat'. Saves chat_log as JSON."""
    export_path = Path("chat_export.json")
    export_path.write_text(json.dumps(chat_log, indent=2), encoding="utf-8")
    return str(export_path)


def use_sample_question(question: str) -> str:
    """Called when the user clicks one of the sample question buttons."""
    return question


# ------------------------------------------------------------------------
# Dark theme styling
# ------------------------------------------------------------------------

CUSTOM_CSS = """
.gradio-container {
    background-color: #0B0F19 !important;
}
#header-box {
    background: #111827;
    border: 1px solid #232B3D;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 10px;
}
#header-box h1 {
    color: #E5E7EB !important;
    font-size: 20px !important;
    margin: 0 !important;
}
#header-box p {
    color: #9CA3AF !important;
    margin: 4px 0 0 0 !important;
}
.sidebar-box {
    background: #111827;
    border: 1px solid #232B3D;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 10px;
}
footer {visibility: hidden}
"""

THEME = gr.themes.Base(primary_hue="indigo", neutral_hue="slate").set(
    body_background_fill="#0B0F19",
    block_background_fill="#111827",
    block_border_color="#232B3D",
    body_text_color="#E5E7EB",
)


# ------------------------------------------------------------------------
# Build the Gradio dashboard
# ------------------------------------------------------------------------

def build_app() -> gr.Blocks:
    with gr.Blocks(title=config.APP_TITLE) as demo:

        with gr.Column(elem_id="header-box"):
            gr.Markdown(f"# 🏢 {config.APP_TITLE}")
            gr.Markdown("Ask questions about real-estate holdings and trades in plain English.")
            status_box = gr.Markdown(loader.get_status_text())

        with gr.Row():
            # ---------------- Sidebar ----------------
            with gr.Column(scale=1):
                with gr.Group(elem_classes="sidebar-box"):
                    gr.Markdown("### 📂 Upload Data")
                    holdings_upload = gr.File(label="holdings.csv", file_types=[".csv"])
                    trades_upload = gr.File(label="trades.csv", file_types=[".csv"])

                with gr.Group(elem_classes="sidebar-box"):
                    gr.Markdown("### 💡 Sample Questions")
                    sample_buttons = [gr.Button(q, size="sm") for q in config.SAMPLE_QUESTIONS]

                with gr.Group(elem_classes="sidebar-box"):
                    gr.Markdown("### 🕘 Chat History")
                    history_box = gr.Markdown("_No questions yet._")

            # ---------------- Main panel ----------------
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Portfolio Assistant", height=400)

                with gr.Row():
                    question_box = gr.Textbox(
                        placeholder="Ask about holdings, trades, PL_YTD, market value...",
                        show_label=False,
                        scale=4,
                    )
                    send_button = gr.Button("Send", variant="primary", scale=1)

                with gr.Row():
                    clear_button = gr.Button("🧹 Clear Chat", size="sm")
                    export_button = gr.Button("⬇️ Export Chat", size="sm")
                    export_file = gr.File(label="Exported file", visible=True)

                chart_output = gr.Plot(label="Chart")

                with gr.Accordion("📊 Data Preview", open=False):
                    with gr.Tab("Holdings"):
                        holdings_preview = gr.Dataframe(value=_preview("holdings"))
                    with gr.Tab("Trades"):
                        trades_preview = gr.Dataframe(value=_preview("trades"))

        # ---------------- Wire everything together ----------------
        holdings_upload.change(
            handle_holdings_upload, inputs=[holdings_upload], outputs=[status_box, holdings_preview]
        )
        trades_upload.change(
            handle_trades_upload, inputs=[trades_upload], outputs=[status_box, trades_preview]
        )

        send_button.click(
            handle_chat,
            inputs=[question_box, chatbot],
            outputs=[chatbot, question_box, chart_output, history_box],
        )
        question_box.submit(
            handle_chat,
            inputs=[question_box, chatbot],
            outputs=[chatbot, question_box, chart_output, history_box],
        )

        clear_button.click(handle_clear_chat, outputs=[chatbot, chart_output, history_box])
        export_button.click(handle_export_chat, outputs=[export_file])

        for button in sample_buttons:
            button.click(use_sample_question, inputs=[button], outputs=[question_box])

    return demo


def main() -> None:
    """Load the sample data and launch the Gradio app."""
    loader.load_default_data()

    if not config.GROQ_API_KEY:
        print("Warning: GROQ_API_KEY is not set. Running in fallback mode (no LLM calls).")

    demo = build_app()
    demo.launch(
        server_name=config.SERVER_NAME,
        server_port=config.SERVER_PORT,
        theme=THEME,
        css=CUSTOM_CSS,
    )


if __name__ == "__main__":
    main()
