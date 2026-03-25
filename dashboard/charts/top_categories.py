from typing import Optional

import pandas as pd
import plotly.express as px
from .utils import tighten, default_height

DEFAULT_BAR_COLOR = "#93c5fd"
SELECTED_BAR_COLOR = "#f59e0b"
MUTED_BAR_COLOR = "#cbd5e1"


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
        text="revenue",
        title="Top 10 Categories (Revenue)",
        labels={"revenue": "Revenue (BRL)", "top_category": "Category"},
        height=height or default_height(),
    )

    fig.update_traces(
        hovertemplate="%{y}<br>Revenue: %{x:,.0f} BRL<br>Orders: %{customdata[0]:,}",
        marker_color=top_cat["bar_color"],
        textfont_size=11,
        textposition="outside",
        cliponaxis=False,
        customdata=top_cat[["orders"]],
    )
    return tighten(fig)
