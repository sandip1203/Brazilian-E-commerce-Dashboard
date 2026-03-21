import pandas as pd
import plotly.express as px
from .utils import tighten, default_height


def delivery_hist_chart(df: pd.DataFrame, key_suffix: str = "", height=None):
    fig = px.histogram(
        df,
        x=df["delivery_days"].clip(upper=60),
        nbins=30,
        text_auto=True,
        title="Delivery Time Distribution (clipped at 60 days)",
        labels={"x": "Delivery Time (days)", "count": "Frequency"},
        height=height or default_height(),
    )
    fig.update_traces(textfont_size=10)
    suffix = f" {key_suffix}".strip()
    fig.update_traces(hovertemplate="%{x:.1f} days: %{y} orders")
    fig.update_layout(title=f"Delivery Time Distribution (clipped at 60 days){suffix}")
    return tighten(fig)
