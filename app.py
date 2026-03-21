from pathlib import Path
import plotly.express as px
import streamlit as st
import altair as alt

from dashboard.data import load_dataset, filter_data
from dashboard.kpis import render_kpis
from dashboard.charts import (
    monthly_revenue_chart,
    top_categories_chart,
    payment_mix_chart,
    delivery_by_state_chart,
    delivery_hist_chart,
    order_map_chart,
    crossfilter_chart,
)

ACCENT_COLOR = "#f59e0b"
BACKGROUND = "#0f172a"
TEXT_COLOR = "#000000"

# Use white chart backgrounds for clarity
px.defaults.template = "plotly_white"
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
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def main():
    apply_theme()
    df = load_dataset()

    main_col, right_col = st.columns([4, 1], gap="large")

    with right_col:
        filters = render_filters(df)

    filtered = filter_data(df, *filters)

    with main_col:
        st.title("Brazilian E-commerce Dashboard")


        render_kpis(filtered)

        map_col, chart_col = st.columns([1.35, 1.45], gap="medium")
        with map_col:

            fig_map = order_map_chart(filtered)
            if fig_map is None:
                st.info("No geolocated orders for current filters.")
            else:
                st.plotly_chart(fig_map, use_container_width=True)
            st.plotly_chart(payment_mix_chart(filtered), use_container_width=True)
            st.plotly_chart(delivery_hist_chart(filtered, key_suffix="Filtered", height=200), use_container_width=True)

        with chart_col:
            # Tableau-style crossfilter (click states to filter lines and categories)
            st.altair_chart(crossfilter_chart(filtered), use_container_width=True)

    with right_col:
        st.plotly_chart(delivery_by_state_chart(filtered, height=260), use_container_width=True)



if __name__ == "__main__":
    main()
