import pandas as pd
import plotly.express as px
from .utils import tighten, default_height


def delivery_by_state_chart(df: pd.DataFrame, height=None):
    delivery_state = (
        df.dropna(subset=["delivery_days"])
        .groupby("customer_state")["delivery_days"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig = px.bar(
        delivery_state,
        x="delivery_days",
        y="customer_state",
        orientation="h",
        text="delivery_days",
        title="Average Delivery Time by State",
        height=height or default_height(),
        color="delivery_days",
        color_continuous_scale="OrRd",
    )

    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        textfont=dict(size=11),
        cliponaxis=False
    )

    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    fig.update_traces(hovertemplate="%{y}: %{x:.1f} days")

    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False)

    return tighten(fig)
