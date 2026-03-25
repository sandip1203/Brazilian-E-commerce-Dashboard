import plotly.express as px
import pandas as pd

# Features to include in correlation matrix (ordered, with letter codes)
CORR_FEATURES = [
    "price",            # A: product price before shipping
    "freight_value",    # B: shipping cost
    "payment_value",    # C: total payment amount (price + freight)
    "product_weight_g", # D: product weight in grams
    "review_score",     # E: customer rating (1-5)
]

LABEL_MAP = {
    "price": "A",
    "freight_value": "B",
    "payment_value": "C",
    "product_weight_g": "D",
    "review_score": "E",
}


def correlation_heatmap(df: pd.DataFrame, height: int | None = None):
    """Return a Plotly heatmap (or None) for the predefined correlation features."""
    usable_cols = [c for c in CORR_FEATURES if c in df.columns]
    if len(usable_cols) < 2 or df.empty:
        return None

    corr = df[usable_cols].corr(numeric_only=True)
    corr = corr.rename(index=LABEL_MAP, columns=LABEL_MAP)

    target_height = height or 240
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        height=target_height,
        labels=dict(color="Correlation (r)"),
    )

    fig.update_layout(
        margin=dict(l=90, r=20, t=18, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(
            title="Correlation (r)",
            ticks="outside",
            tickmode="array",
            tickvals=[-1, -0.5, 0, 0.5, 1],
            len=0.7,
            thickness=14,
        ),
    )
    fig.update_xaxes(side="top", tickangle=0, tickfont=dict(size=11))
    fig.update_yaxes(tickfont=dict(size=11))

    legend_text = (
        "<b>Legend</b><br>"
        "A = price<br>"
        "B = freight_value<br>"
        "C = payment_value<br>"
        "D = product_weight_g<br>"
        "E = review_score"
    )
    fig.add_annotation(
        x=-0.2,   # a bit left of the matrix
        y=0.6,     # slightly above center
        xref="paper",
        yref="paper",
        align="left",
        showarrow=False,
        text=legend_text,
        font=dict(size=10, color="#4b5563"),
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor="rgba(0,0,0,0.1)",
        borderwidth=1,
        borderpad=6,
    )
    return fig
