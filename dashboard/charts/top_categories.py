from typing import Optional

import pandas as pd
import plotly.express as px
from .utils import tighten, default_height

DEFAULT_BAR_COLOR = "#60a5fa"
SELECTED_BAR_COLOR = "#f59e0b"
MUTED_BAR_COLOR = "#bfdbfe"


def top_categories_chart(
    df: pd.DataFrame,
    *,
    height: Optional[int] = None,
    selected_category: Optional[str] = None,
):
    """Horizontal bar chart of the top 10 categories by revenue.

    A height can be supplied to better fit different layout slots; defaults
    to the shared chart height used elsewhere.
    """

    top_cat = (
        df.groupby("top_category")
        .agg(revenue=("order_value", "sum"), orders=("order_id", "nunique"))
        .nlargest(10, "revenue")
        .reset_index()
    )

    if top_cat.empty:
        fig = px.bar(
            top_cat,
            x="revenue",
            y="top_category",
            orientation="h",
            title="Top 10 Categories (Revenue)",
            labels={"revenue": "Revenue (BRL)", "top_category": "Category"},
            height=height or default_height(),
        )
        return tighten(fig)

    top_cat["revenue_label"] = top_cat["revenue"].map(lambda value: f"{value:,.0f}")
    top_cat["hover_text"] = top_cat.apply(
        lambda row: (
            f"{row['top_category']}<br>"
            f"Revenue: BRL {row['revenue']:,.2f}<br>"
            f"Orders: {int(row['orders']):,}"
        ),
        axis=1,
    )

    if selected_category:
        top_cat["bar_color"] = top_cat["top_category"].apply(
            lambda category: SELECTED_BAR_COLOR if category == selected_category else MUTED_BAR_COLOR
        )
    else:
        top_cat["bar_color"] = DEFAULT_BAR_COLOR

    fig = px.bar(
        top_cat,
        x="revenue",
        y="top_category",
        orientation="h",
        text="revenue_label",
        title="Top 10 Categories (Revenue)",
        labels={"revenue": "Revenue (BRL)", "top_category": "Category"},
        height=height or default_height(),
    )

    max_revenue = float(top_cat["revenue"].max())
    tick_count = 5
    tickvals = [max_revenue * i / (tick_count - 1) for i in range(tick_count)] if max_revenue else [0]
    ticktext = [f"{value:,.0f}" for value in tickvals]

    fig.update_traces(
        hovertext=top_cat["hover_text"],
        hovertemplate="%{hovertext}<extra></extra>",
        marker_color=top_cat["bar_color"],
        marker_line_color="#1e3a5f",
        marker_line_width=1.2,
        textfont_size=11,
        textfont_color="#1e3a5f",
        textposition="outside",
        cliponaxis=False,
        opacity=0.95,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
        range=[0, max_revenue * 1.18],
        automargin=True,
    )
    fig.update_yaxes(automargin=True)
    return tighten(fig)
