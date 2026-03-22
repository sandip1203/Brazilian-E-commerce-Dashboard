from typing import Optional

import pandas as pd
import plotly.express as px
from .utils import tighten, default_height


def monthly_revenue_chart(df: pd.DataFrame, height: Optional[int] = None):
    month_rev = (
        df.groupby("year_month")["order_value"]
        .sum()
        .reset_index()
        .sort_values("year_month")
    )
    fig = px.line(
        month_rev,
        x="year_month",
        y="order_value",
        markers=True,
        title="Monthly Revenue Trend",
        labels={"order_value": "Revenue (BRL)", "year_month": "Year-Month"},
        height=height or default_height(),
    )
    fig.update_traces(hovertemplate="Revenue: %{y:,.0f}<br>Month: %{x}")
    return tighten(fig)
