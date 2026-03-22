import pandas as pd
import plotly.express as px
from .utils import tighten, default_height


def revenue_state_chart(df: pd.DataFrame, height=None):
    data = (
        df.groupby("customer_state")["order_value"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig = px.bar(
        data,
        y="customer_state",
        x="order_value",
        orientation="h",
        title="Revenue by State",
        labels={"customer_state": "State", "order_value": "Revenue (BRL)"},
        height=height or default_height(),
        color="order_value",
color_continuous_scale="Viridis",

    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(
        texttemplate="%{x:,.0f}",
        textposition="outside",
        hovertemplate="%{y}: %{x:,.0f} BRL",
        cliponaxis=False,
    )
    return tighten(fig)
