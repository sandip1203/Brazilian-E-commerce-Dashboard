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

    cards = [
        ("💰", "Total Revenue", f"{total_revenue/1_000_000:,.2f} M BRL", "Filtered view"),
        ("📦", "Total Orders", f"{orders:,}", "Unique orders"),
        ("💳", "Avg Order Value", f"{avg_order_value:,.0f} BRL", "Per order"),
        ("⏱️", "On-Time Delivery Rate", f"{on_time_rate:.0%}", "Delivered on/early"),
        ("⭐", "Avg Review Score", f"{avg_review:,.2f}", "Customer ratings"),
    ]

    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"]:has(div.kpi-card) {
            margin-top: -0.35rem !important;
            margin-bottom: -0.5rem !important;
        }
        .kpi-card {
            padding: 6px 10px;
            border-radius: 8px;
            background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        }
        .kpi-label { font-size: 12px; color: #475569; font-weight: 600; line-height: 1.2; }
        .kpi-value { font-size: 20px; color: #0f172a; font-weight: 800; margin-top: 2px; line-height: 1.15; }
        .kpi-sub { font-size: 10px; color: #94a3b8; margin-top: 1px; line-height: 1.2; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(len(cards))
    for col, (icon, label, value, sub) in zip(cols, cards):
        col.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{icon} {label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
