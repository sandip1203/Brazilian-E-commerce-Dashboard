import streamlit as st


def render_kpis(df):
    total_revenue = df["order_value"].sum()
    orders = df["order_id"].nunique()
    avg_order_value = total_revenue / orders if orders else 0

    delivered = df.dropna(subset=["delay_days"])
    on_time = delivered[delivered["delay_days"] <= 0]
    on_time_rate = (len(on_time) / len(delivered)) if len(delivered) else 0
    avg_review = df["review_score"].dropna().mean()
    avg_delay_late = delivered[delivered["delay_days"] > 0]["delay_days"].mean() if not delivered.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Revenue", f"{total_revenue:,.0f} BRL")
    col2.metric("Total Orders", f"{orders:,}")
    col3.metric("Avg Order Value", f"{avg_order_value:,.0f} BRL")
    col4.metric("On-Time Delivery Rate", f"{on_time_rate:.0%}")
    col5.metric("Avg Review Score", f"{avg_review:,.2f}")

