from typing import Optional

import pandas as pd
import plotly.express as px
from .utils import tighten, default_height


def top_categories_chart(df: pd.DataFrame, *, height: Optional[int] = None):
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

    fig = px.bar(
        top_cat,
        x="revenue",
        y="top_category",
        orientation="h",
        text="revenue",
        title="Top 10 Categories (Revenue)",
        labels={"revenue": "Revenue (BRL)", "top_category": "Category"},
        height=height or default_height(),
        color="revenue",
        color_continuous_scale="Blues",
    )

    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(
        hovertemplate="%{y}<br>Revenue: %{x:,.0f} BRL<br>Orders: %{customdata[0]:,}",

        textfont_size=11,
        textposition="outside",
        cliponaxis=False,
        customdata=top_cat[["orders"]],
    )
    return tighten(fig)
