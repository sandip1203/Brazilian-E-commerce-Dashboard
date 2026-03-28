import plotly.express as px
import pandas as pd
import streamlit as st
from dashboard.data import load_dataset, filter_data
from dashboard.kpis import render_kpis
from dashboard.charts import correlation_heatmap
from dashboard.charts import (
    monthly_revenue_chart,
    top_categories_chart,
    payment_mix_chart,
    delivery_hist_chart,
    review_timeliness_chart,
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
    month_options = [
        "2017-01",
        "2017-02",
        "2017-03",
        "2017-04",
        "2017-05",
        "2017-06",
        "2017-07",
        "2017-08",
        "2017-09",
        "2017-10",
        "2017-11",
        "2017-12",
        "2018-01",
        "2018-02",
        "2018-03",
        "2018-04",
        "2018-05",
        "2018-06",
        "2018-07",
        "2018-08",
    ]
    default_months = month_options[-6:] if len(month_options) > 6 else month_options
    month_choice = st.multiselect("Order Year-Month", options=month_options, default=default_months)

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

    status_options = ["On Time", "Late"]
    status_choice = st.multiselect("Delivery status", options=status_options, default=[])

    return month_choice, state_choice, category_choice, payment_choice, review_choice, status_choice


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

    (
        month_choice,
        state_choice,
        category_choice,
        payment_choice,
        review_choice,
        status_choice,
    ) = filters

    filtered = filter_data(df, *filters)
    selected_category = st.session_state.get("selected_category")
    filtered_for_click = (
        filtered[filtered["top_category"] == selected_category]
        if selected_category
        else filtered
    )

    # KPI data should always include the previous month for comparison when only one month is selected.
    kpi_months = list(month_choice)
    if len(kpi_months) == 1:
        current_period = pd.Period(kpi_months[0], freq="M")
        prev_period = (current_period - 1).strftime("%Y-%m")
        if prev_period in df["year_month"].unique():
            kpi_months = [prev_period, kpi_months[0]]
    kpi_df = filter_data(
        df,
        kpi_months,
        state_choice,
        category_choice,
        payment_choice,
        review_choice,
        status_choice,
    )
    if selected_category:
        kpi_df = kpi_df[kpi_df["top_category"] == selected_category]

    with main_col:


        render_kpis(kpi_df)
        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

        row1_col1, row1_col2 = st.columns(2, gap="medium")
        with row1_col1:
            chart_card(
                "Review Score vs Delivery Timeliness",
                review_timeliness_chart(filtered_for_click, height=CHART_HEIGHT),
            )
        with row1_col2:
            chart_card(
                "Monthly Revenue Trend",
                monthly_revenue_chart(filtered_for_click, height=CHART_HEIGHT),
            )

        # Interactive category filter (click a bar to filter all charts)
        def render_category_selector(dataframe, current_selection=None):
            fig = top_categories_chart(
                dataframe,
                height=CHART_HEIGHT,
                selected_category=current_selection,
            )
            with bordered_container():
                st.markdown(
                    '<div class="chart-title">Top Categories (click to filter)</div>',
                    unsafe_allow_html=True,
                )
                component_key = f"top_category_click_{current_selection or 'none'}"
                event = st.plotly_chart(
                    set_fig_background(fig),
                    use_container_width=True,
                    key=component_key,
                    on_select="rerun",
                    selection_mode="points",
                    config={"displayModeBar": False},
                )
                points = event.selection.points if event else []
                if points:
                    chosen = points[0].get("y") or points[0].get("label")
                    if chosen:
                        new_selection = None if current_selection == chosen else chosen
                        if st.session_state.get("selected_category") != new_selection:
                            st.session_state["selected_category"] = new_selection
                            st.rerun()

        row2_col1, row2_col2 = st.columns(2, gap="medium")
        with row2_col1:
            render_category_selector(filtered, selected_category)

        selected_category = st.session_state.get("selected_category")

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
            corr_fig = correlation_heatmap(filtered_for_click, height=CHART_HEIGHT)
            if corr_fig:
                chart_card(
                    "Correlation Heatmap (A–E)",
                    corr_fig,
                )
            else:
                st.info(
                    "Not enough numeric data to compute correlations for the selected filters.",
                    icon="ℹ️",
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
