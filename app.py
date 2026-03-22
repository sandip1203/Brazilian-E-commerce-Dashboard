import plotly.express as px
import streamlit as st
from dashboard.data import load_dataset, filter_data
from dashboard.kpis import render_kpis
try:
    # Enables click-to-filter on Plotly charts inside Streamlit
    from streamlit_plotly_events import plotly_events
except ImportError:  # pragma: no cover - runtime dependency
    plotly_events = None
from dashboard.charts import (
    monthly_revenue_chart,
    top_categories_chart,
    payment_mix_chart,
    delivery_by_state_chart,
    delivery_hist_chart,
    revenue_state_chart,
)

ACCENT_COLOR = "#f59e0b"
BACKGROUND = "transparent"
TEXT_COLOR = "inherit"
CHART_HEIGHT = 180
# Shown in the browser tab, the “About” menu, and (via CSS) the top app header bar
APP_TITLE = "Brazilian E-commerce Dashboard"
# Top nav bar (Streamlit header chrome)
NAV_BAR_BG = (
    "linear-gradient(135deg, #0f172a 0%, #1e3a5f 42%, #1e293b 100%)"
)
NAV_BAR_TEXT = "#f8fafc"


def _css_single_quoted(s: str) -> str:
    """Escape a string for safe use inside CSS single-quoted content: '...'."""
    return s.replace("\\", "\\\\").replace("'", "\\'")
CORR_FEATURES = [
    "price",
    "freight_value",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
    "payment_value",
    "review_score",
]

# Use transparent backgrounds so the app can sit on light or dark themes
px.defaults.color_discrete_sequence = px.colors.qualitative.Vivid

st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    page_icon="📦",
)


def apply_theme():
    title_css = _css_single_quoted(APP_TITLE)
    st.markdown(
        f"""
        <style>
            .main {{ background-color: {BACKGROUND}; color: {TEXT_COLOR}; }}
            .stMetric label, .stCheckbox, .stSelectbox, .stSlider {{ color: {TEXT_COLOR}; }}
            /* Slightly tighter gap below the nav bar */
            .block-container {{ padding-top: 1.15rem; padding-bottom: 0.6rem; }}
            /* Extra top padding so title/KPIs clear the Streamlit nav bar */
            section[data-testid="stSidebar"] > div:first-child {{ padding-top: 1.6rem; }}
            h1, h2, h3, h4, h5, h6 {{ color: {TEXT_COLOR}; font-weight: 700; }}
            .side-card {{
                margin-top: 12px;
                padding: 10px 12px;
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(0,0,0,0.15);
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.12);
                backdrop-filter: blur(6px);
            }}
            .chart-title {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-weight: 700;
                font-size: 14px;
                color: {TEXT_COLOR};
                margin: 4px 0 6px 2px;
                letter-spacing: 0.01em;
                text-transform: uppercase;
            }}
            /* Right-column filters: clear the top app nav so the heading stays visible */
            .filters-panel {{
                margin-top: 2.25rem;
            }}
            /* Colored top nav bar + centered app title (compact height) */
            header[data-testid="stHeader"] {{
                position: relative;
                min-height: 2.35rem !important;
                background: {NAV_BAR_BG};
                border-bottom: 2px solid {ACCENT_COLOR};
                box-shadow: 0 2px 14px rgba(15, 23, 42, 0.45);
            }}
            header[data-testid="stHeader"] [data-testid="stToolbar"] {{
                position: relative;
                z-index: 1;
                color: {NAV_BAR_TEXT};
            }}
            header[data-testid="stHeader"] [data-testid="stToolbar"] button {{
                color: {NAV_BAR_TEXT} !important;
            }}
            header[data-testid="stHeader"]::before {{
                content: '{title_css}';
                position: absolute;
                left: 0;
                right: 0;
                top: 0;
                bottom: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0 4.5rem;
                box-sizing: border-box;
                font-weight: 700;
                font-size: 0.98rem;
                letter-spacing: 0.02em;
                color: {NAV_BAR_TEXT};
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
                pointer-events: none;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                z-index: 0;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"] {{
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.12);
                padding: 10px 14px 10px 14px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_plotly_theme():
    """Match Plotly template to Streamlit theme for readable axes."""
    try:
        base = st.get_option("theme.base") or "light"
    except Exception:
        base = "light"
    px.defaults.template = "plotly_dark" if base == "dark" else "plotly_white"


def render_filters(df):
    st.markdown(
        '<div class="filters-panel"><h3>Filters</h3></div>',
        unsafe_allow_html=True,
    )
    min_date = df["order_purchase_timestamp"].min().date()
    max_date = df["order_purchase_timestamp"].max().date()
    date_range = st.slider("Order date range", min_date, max_date, (min_date, max_date))

    states = sorted(df["customer_state"].dropna().unique())
    default_states = states if len(states) <= 8 else states[:8]
    state_choice = st.multiselect("Customer state", options=states, default=default_states)

    categories = df["top_category"].dropna().value_counts().head(12).index.tolist()
    category_choice = st.multiselect("Product category", options=categories, default=[])

    payment_options = sorted(
        {p.strip() for vals in df["payment_types"].dropna() for p in vals.split(",")}
    )
    payment_choice = st.multiselect("Payment type", options=payment_options, default=[])

    review_choice = st.slider("Review score", 1.0, 5.0, (1.0, 5.0), step=0.5)

    status_options = ["On Time", "Late", "Unknown"]
    status_choice = st.multiselect("Delivery status", options=status_options, default=[])

    return date_range, state_choice, category_choice, payment_choice, review_choice, status_choice


def correlation_heatmap(df):
    usable_cols = [c for c in CORR_FEATURES if c in df.columns]
    if len(usable_cols) < 2 or df.empty:
        return None
    corr = df[usable_cols].corr(numeric_only=True)
    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        height=220,
        labels=dict(color="Corr"),

    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(side="top")
    return fig


def bordered_container():
    """Streamlit >=1.29 supports border arg; fallback gracefully on older versions."""
    try:
        return st.container(border=True)
    except TypeError:
        return st.container()


def set_fig_background(fig):
    """Give Plotly charts a light card-friendly background."""
    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,0.94)",
        plot_bgcolor="rgba(255,255,255,0.94)",
    )
    return fig


def chart_card(title, fig, key=None):
    """Render a Plotly figure inside a styled card with a small heading."""
    with bordered_container():
        st.plotly_chart(set_fig_background(fig), use_container_width=True, key=key)


def main():
    apply_theme()
    apply_plotly_theme()
    df = load_dataset()

    main_col, right_col = st.columns([4, 1], gap="large")

    with right_col:
        filters = render_filters(df)
        corr_box = st.container()

    filtered = filter_data(df, *filters)
    selected_category = st.session_state.get("selected_category")
    filtered_for_click = (
        filtered[filtered["top_category"] == selected_category]
        if selected_category
        else filtered
    )

    with corr_box:
        corr_fig = correlation_heatmap(filtered_for_click)
        if corr_fig:
            with bordered_container():
                st.markdown(
                    '<div class="chart-title">Correlation Heatmap</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(set_fig_background(corr_fig), use_container_width=True)

    with main_col:


        render_kpis(filtered_for_click)
        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

        row1_col1, row1_col2 = st.columns(2, gap="medium")
        with row1_col1:
            chart_card(
                "Revenue by State",
                revenue_state_chart(filtered_for_click, height=CHART_HEIGHT),
            )
        with row1_col2:
            chart_card(
                "Monthly Revenue Trend",
                monthly_revenue_chart(filtered_for_click, height=CHART_HEIGHT),
            )

        # Interactive category filter (click a bar to filter all charts)
        def render_category_selector(dataframe, current_selection=None):
            fig = top_categories_chart(dataframe, height=CHART_HEIGHT)
            with bordered_container():
                st.markdown(
                    '<div class="chart-title">Top Categories (click to filter)</div>',
                    unsafe_allow_html=True,
                )
                if plotly_events:
                    events = plotly_events(
                        fig,
                        click_event=True,
                        hover_event=False,
                        select_event=False,
                        key="top_category_click",
                        override_height=CHART_HEIGHT,
                    )
                    if events:
                        chosen = events[0].get("y") or events[0].get("label")
                        if chosen:
                            if current_selection and chosen == current_selection:
                                st.session_state["selected_category"] = None
                            else:
                                st.session_state["selected_category"] = chosen
                else:
                    st.plotly_chart(set_fig_background(fig), use_container_width=True)
                    if st.session_state.get("selected_category") is None:
                        st.info(
                            "Install `streamlit-plotly-events` for click-to-filter: "
                            "`pip install streamlit-plotly-events`",
                            icon="🖱️",
                        )

        row2_col1, row2_col2 = st.columns(2, gap="medium")
        with row2_col1:
            render_category_selector(filtered, selected_category)
            if selected_category := st.session_state.get("selected_category"):
                st.caption(
                    f"Filtering category: {selected_category} (click same bar to clear)"
                )
        # Apply interactive category filter to downstream charts
        filtered_for_click = (
            filtered[filtered["top_category"] == selected_category]
            if selected_category
            else filtered
        )

        with row2_col2:
            chart_card(
                "Payment Mix",
                payment_mix_chart(filtered_for_click, height=CHART_HEIGHT),
            )

        row3_col1, row3_col2 = st.columns(2, gap="medium")
        with row3_col1:
            chart_card(
                "Delivery Performance by State",
                delivery_by_state_chart(filtered_for_click, height=CHART_HEIGHT),
            )
        with row3_col2:
            chart_card(
                "Delivery Time Distribution",
                delivery_hist_chart(
                    filtered_for_click, key_suffix="Filtered", height=CHART_HEIGHT
                ),
            )


if __name__ == "__main__":
    main()
