import plotly.express as px


def tighten(fig, top=30, bottom=10):
    fig.update_layout(
        margin=dict(l=8, r=8, t=top, b=bottom),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        showlegend=False,
    )
    return fig


def default_height():
    return 200
