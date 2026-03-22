import plotly.express as px


def tighten(fig, top=30, bottom=10):
    fig.update_layout(
        margin=dict(l=8, r=8, t=top, b=bottom),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        showlegend=False,
    )
    return fig


def default_height():
    """Shared default height for all charts to keep layout uniform."""
    return 240
