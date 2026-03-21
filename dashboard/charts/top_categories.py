import pandas as pd
import plotly.express as px
from .utils import tighten, default_height


def top_categories_chart(df: pd.DataFrame):
    top_cat = (
        df.groupby("top_category")["order_id"]
        .nunique()
        .nlargest(10)
        .reset_index()
        .rename(columns={"order_id": "orders"})
    )
    fig = px.bar(
        top_cat,
        x="orders",
        y="top_category",
        orientation="h",
        text_auto=True,
        title="Top 10 Categories (Orders)",
        labels={"orders": "Orders", "top_category": "Category"},
        height=default_height(),
        color="orders",
        color_continuous_scale="Blues",
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(
        hovertemplate="%{y}: %{x:,.0f} orders",
    )
    fig.update_traces(textfont_size=11, textposition="outside", cliponaxis=False)
    return tighten(fig)
