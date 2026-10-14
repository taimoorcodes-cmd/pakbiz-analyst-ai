# agents/nodes/chart_node.py
# Auto-detects best Plotly chart type + KPI support for single-value results

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from agents.state import AgentState

COLORS = ['#2563EB', '#7C3AED', '#059669',
          '#D97706', '#DC2626']


def chart_node(state: AgentState) -> AgentState:
    try:
        df = state.get("sql_result")
        pkr_cols = state.get("pkr_columns", [])

        if df is None or df.empty:
            state["status"] = "output"
            return state

        # --- KPI branch: single-value result ---
        # If result has only 1 row and 1-2 columns, skip chart and show KPI
        if len(df) == 1 and df.shape[1] <= 2:
            kpi_value = df.iloc[0, -1]
            kpi_label = df.columns[-1].replace("_", " ").title()
            sub_label = None
            if df.shape[1] == 2:
                sub_label = str(df.iloc[0, 0])
            state["chart_data"] = {
                "type": "kpi",
                "value": kpi_value,
                "label": kpi_label,
                "sub_label": sub_label,
            }
            state["status"] = "chart_ready"
            return state

        fig = auto_create_chart(df, pkr_cols)
        state["chart_data"] = fig
        state["status"] = "chart_ready"
        return state

    except Exception as e:
        state["error"] = f"Chart error: {str(e)}"
        state["status"] = "output"
        return state


def auto_create_chart(df: pd.DataFrame, pkr_cols: list):
    cols = df.columns.tolist()
    dtypes = df.dtypes

    num_cols = [
        c for c in cols
        if pd.api.types.is_numeric_dtype(dtypes[c])
    ]
    str_cols = [
        c for c in cols
        if pd.api.types.is_string_dtype(dtypes[c])
        or pd.api.types.is_object_dtype(dtypes[c])
    ]
    date_cols = [
        c for c in cols
        if pd.api.types.is_datetime64_any_dtype(dtypes[c])
    ]

    # Date + number = line chart (time series)
    if date_cols and num_cols:
        fig = px.line(
            df, x=date_cols[0], y=num_cols[0],
            title=f"{num_cols[0]} over time",
            color_discrete_sequence=COLORS,
            template="plotly_white"
        )
        return _format_pkr(fig, num_cols[0], pkr_cols)

    # Text + number = bar chart (top 15 only for readability)
    if str_cols and num_cols:
        plot_df = df.nlargest(
            15, num_cols[0]) if len(df) > 15 else df
        plot_df = plot_df.sort_values(
            by=num_cols[0], ascending=False
        )
        fig = px.bar(
            plot_df, x=str_cols[0], y=num_cols[0],
            title=f"{num_cols[0]} by {str_cols[0]}",
            color=num_cols[0],
            color_continuous_scale='Blues',
            template="plotly_white"
        )
        # Smart label rotation: horizontal if <= 8 bars, else -30 degrees
        n_bars = len(plot_df)
        angle = 0 if n_bars <= 8 else -30
        fig.update_xaxes(tickangle=angle)
        return _format_pkr(fig, num_cols[0], pkr_cols)

    # Two numbers = scatter
    if len(num_cols) >= 2:
        fig = px.scatter(
            df, x=num_cols[0], y=num_cols[1],
            title=f"{num_cols[0]} vs {num_cols[1]}",
            color_discrete_sequence=COLORS,
            template="plotly_white"
        )
        return fig

    # One number = histogram
    if len(num_cols) == 1:
        fig = px.histogram(
            df, x=num_cols[0],
            title=f"Distribution of {num_cols[0]}",
            color_discrete_sequence=COLORS,
            template="plotly_white"
        )
        return _format_pkr(fig, num_cols[0], pkr_cols)

    # Many numbers = heatmap
    if len(num_cols) > 2:
        corr = df[num_cols].corr()
        fig = px.imshow(
            corr, title="Correlation Heatmap",
            color_continuous_scale='RdBu',
            template="plotly_white"
        )
        return fig

    # Fallback = table
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df.columns),
            fill_color='#2563EB',
            font=dict(color='white'),
            align='left'
        ),
        cells=dict(
            values=[df[c] for c in df.columns],
            fill_color='#F8FAFC',
            align='left'
        )
    )])
    fig.update_layout(title="Query Results")
    return fig


def _format_pkr(fig, col_name, pkr_cols):
    if col_name in pkr_cols:
        fig.update_layout(
            yaxis_tickprefix='Rs ',
            yaxis_tickformat=','
        )
    return fig