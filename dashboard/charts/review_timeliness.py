from typing import Optional

import pandas as pd
import plotly.graph_objects as go

from .utils import default_height, tighten

REVIEW_SCORE_ORDER = [1, 2, 3, 4, 5]
BOX_COLORS = {
    1: "#ef4444",
    2: "#f97316",
    3: "#f59e0b",
    4: "#84cc16",
    5: "#22c55e",
}


def review_timeliness_chart(df: pd.DataFrame, height: Optional[int] = None):
    plot_df = df.dropna(subset=["delay_days", "review_score"]).copy()
    plot_df["delay_days"] = pd.to_numeric(plot_df["delay_days"], errors="coerce")
    plot_df["review_score"] = pd.to_numeric(plot_df["review_score"], errors="coerce")
    plot_df = plot_df.dropna(subset=["delay_days", "review_score"])
    plot_df["review_score_group"] = (
        plot_df["review_score"].round().clip(lower=1, upper=5).astype("Int64")
    )
    plot_df = plot_df[plot_df["review_score_group"].isin(REVIEW_SCORE_ORDER)].copy()

    if plot_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Delivery Delay vs Review Score",
            height=height or default_height(),
        )
        fig.add_annotation(
            text="No delivery-delay data available for the selected filters.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
        return tighten(fig)

    fig = go.Figure()
    for score in REVIEW_SCORE_ORDER:
        values = plot_df.loc[plot_df["review_score_group"] == score, "delay_days"]
        fig.add_trace(
            go.Box(
                y=values,
                name=str(score),
                boxpoints="outliers",
                marker_color=BOX_COLORS[score],
                line=dict(color=BOX_COLORS[score], width=1.5),
                fillcolor=BOX_COLORS[score],
                opacity=0.45,
                hovertemplate="Review score: %{x}<br>Delay: %{y:.1f} days<extra></extra>",
            )
        )

    fig.update_layout(
        title="Delivery Delay vs Review Score",
        height=height or default_height(),
        xaxis_title="Review Score",
        yaxis_title="Delivery Delay (days)",
        showlegend=False,
    )
    fig.update_xaxes(
        categoryorder="array",
        categoryarray=[str(score) for score in REVIEW_SCORE_ORDER],
    )
    fig.update_yaxes(
        zeroline=False,
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.2)",
    )

    fig = tighten(fig, top=36, bottom=48)
    fig.update_yaxes(
        zeroline=False,
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.2)",
    )
    return fig
