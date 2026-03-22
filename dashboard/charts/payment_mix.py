import pandas as pd
import plotly.express as px
from .utils import tighten, default_height


def payment_mix_chart(df: pd.DataFrame, height=None):
    pay_mix = (
        df.assign(payment_types=df["payment_types"].fillna("Unknown"))
        .groupby("payment_types")["order_value"]
        .sum()
        .reset_index()
        .sort_values("order_value", ascending=False)
    )
    fig = px.pie(
        pay_mix,
        names="payment_types",
        values="order_value",
        hole=0.25,
        title="Payment Method Distribution",
        height=height or default_height(),
    )

    fig.update_traces(textposition="inside", texttemplate="%{label}<br>%{percent:.1%}", hovertemplate="%{label}: %{percent:.1%}")
    fig.update_layout(showlegend=True)

    return tighten(fig)
