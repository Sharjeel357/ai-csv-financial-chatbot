"""
Turns a computed result (from compute.py) into a simple bar chart,
using Plotly so it renders nicely and interactively inside Gradio.

Not every result needs a chart — a single number (like "total holdings
= 42") has nothing to plot. We only build a chart when the result has
a table (a breakdown across portfolios or years).
"""

import pandas as pd
import plotly.graph_objects as go

CHART_COLOR = "#6366F1"


def build_chart(result: dict):
    """Build a Plotly bar chart from a result dictionary, or return None."""
    if result.get("is_guarded"):
        return None

    table = result.get("table")
    if not table:
        return None

    data_frame = pd.DataFrame(table)
    if data_frame.empty:
        return None

    label_column = data_frame.columns[0]
    numeric_columns = [
        col for col in data_frame.columns[1:] if pd.api.types.is_numeric_dtype(data_frame[col])
    ]
    if not numeric_columns:
        return None

    value_column = numeric_columns[0]
    # Keep the chart readable — show at most the top 15 bars.
    data_frame = data_frame.sort_values(by=value_column, ascending=True).tail(15)

    figure = go.Figure(
        data=[
            go.Bar(
                x=data_frame[value_column],
                y=data_frame[label_column].astype(str),
                orientation="h",
                marker_color=CHART_COLOR,
                text=data_frame[value_column].apply(lambda v: f"{v:,.0f}"),
                textposition="outside",
            )
        ]
    )

    figure.update_layout(
        template="plotly_dark",
        title=f"{result.get('metric', 'Result')} — breakdown",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#E5E7EB"),
        margin=dict(l=40, r=20, t=50, b=40),
        height=380,
    )

    return figure
