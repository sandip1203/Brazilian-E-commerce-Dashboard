from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .utils import default_height, tighten

BUCKET_ORDER = [
    "Early >14d",
    "Early 7-14d",
    "Early 0-7d",
    "Late 1-7d",
    "Late 8-14d",
    "Late >14d",
]

COLOR_MAP = {
    "Early": "#22c55e",
    "Late": "#ef4444",
}


def review_timeliness_chart(df: pd.DataFrame, height: Optional[int] = None):
    plot_df = df.dropna(subset=["delivery_bucket", "review_score"]).copy()
    plot_df["review_score"] = pd.to_numeric(plot_df["review_score"], errors="coerce")
    plot_df = plot_df.dropna(subset=["review_score"])
    plot_df = plot_df[plot_df["delivery_bucket"].isin(BUCKET_ORDER)].copy()

    if plot_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Review Score vs Delivery Timeliness",
            height=height or default_height(),
        )
        fig.add_annotation(
            text="No review-score data available for the selected filters.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
        return tighten(fig)

    valid_labels = [
        bucket
        for bucket in BUCKET_ORDER
        if (plot_df["delivery_bucket"] == bucket).any()
    ]
    plot_df = plot_df[plot_df["delivery_bucket"].isin(valid_labels)].copy()
    plot_df["delivery_bucket"] = pd.Categorical(
        plot_df["delivery_bucket"],
        categories=valid_labels,
        ordered=True,
    )
    plot_df["timing_group"] = np.where(
        plot_df["delivery_bucket"].astype(str).str.startswith("Early"),
        "Early",
        "Late",
    )

    fig = px.box(
        plot_df,
        x="delivery_bucket",
        y="review_score",
        color="timing_group",
        points="outliers",
        title="Review Score vs Delivery Timeliness",
        labels={
            "delivery_bucket": "Delivery Timing",
            "review_score": "Review Score",
            "timing_group": "",
        },
        category_orders={
            "delivery_bucket": valid_labels,
            "timing_group": ["Early", "Late"],
        },
        color_discrete_map=COLOR_MAP,
        height=height or default_height(),
    )

    fig.update_traces(
        selector=dict(type="box"),
        opacity=0.6,
        marker=dict(size=4, opacity=0.25),
        line=dict(width=1.5),
    )
    fig.update_layout(
        legend_title_text=None,
        yaxis_range=[1, 5.5],
    )
    fig.update_xaxes(
        tickangle=25,
        categoryorder="array",
        categoryarray=valid_labels,
    )
    fig.update_yaxes(dtick=1)

    fig = tighten(fig, top=36, bottom=48)
    fig.update_layout(showlegend=True)
    return fig
