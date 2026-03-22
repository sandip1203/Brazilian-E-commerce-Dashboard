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
CHART_HEIGHT = 200
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
    page_title="Brazilian E-commerce Dashboard",
    layout="wide",
    page_icon="📦",
)


def apply_theme():
    st.markdown(
        f"""
        <style>
            .main {{ background-color: {BACKGROUND}; color: {TEXT_COLOR}; }}
            .stMetric label, .stCheckbox, .stSelectbox, .stSlider {{ color: {TEXT_COLOR}; }}
            .block-container {{ padding-top: 1.6rem; padding-bottom: 0.6rem; }}
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
    st.markdown("### Filters")
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
            st.markdown('<div class="side-card">', unsafe_allow_html=True)
            st.plotly_chart(corr_fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with main_col:
        st.title("Brazilian E-commerce Dashboard")

        render_kpis(filtered_for_click)
        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

        row1_col1, row1_col2 = st.columns(2, gap="medium")
        with row1_col1:
            st.plotly_chart(
                revenue_state_chart(filtered_for_click, height=CHART_HEIGHT),
                use_container_width=True,
            )
        with row1_col2:
            st.plotly_chart(
                monthly_revenue_chart(filtered_for_click, height=CHART_HEIGHT),
                use_container_width=True,
            )

        # Interactive category filter (click a bar to filter all charts)
        def render_category_selector(dataframe, current_selection=None):
            fig = top_categories_chart(dataframe, height=CHART_HEIGHT)
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
                st.plotly_chart(fig, use_container_width=True)
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
            st.plotly_chart(
                payment_mix_chart(filtered_for_click, height=CHART_HEIGHT),
                use_container_width=True,
            )

        row3_col1, row3_col2 = st.columns(2, gap="medium")
        with row3_col1:
            st.plotly_chart(
                delivery_by_state_chart(filtered_for_click, height=CHART_HEIGHT),
                use_container_width=True,
            )
        with row3_col2:
            st.plotly_chart(
                delivery_hist_chart(
                    filtered_for_click, key_suffix="Filtered", height=CHART_HEIGHT
                ),
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
