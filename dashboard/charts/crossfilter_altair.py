import altair as alt
import pandas as pd


def crossfilter_chart(df: pd.DataFrame):
    base = df.copy()

    state_sel = alt.selection_multi(fields=["customer_state"], on="click", clear="true")

    bar_states = (
        alt.Chart(base)
        .mark_bar()
        .encode(
            y=alt.Y("customer_state:N", sort="-x", title="State"),
            x=alt.X("sum(order_value):Q", title="Revenue (BRL)"),
            color=alt.condition(state_sel, alt.Color("customer_state:N", legend=None), alt.value("#d3d3d3")),
            tooltip=[
                alt.Tooltip("customer_state:N", title="State"),
                alt.Tooltip("sum(order_value):Q", title="Revenue", format=",.0f"),
            ],
        )
        .add_params(state_sel)
        .properties(height=140, title="Revenue by state")
    )

    line_month = (
        alt.Chart(base)
        .mark_line(point=True)
        .encode(
            x=alt.X("yearmonth(order_purchase_timestamp):T", title="Month"),
            y=alt.Y("sum(order_value):Q", title="Revenue (BRL)"),
            color=alt.Color("customer_state:N", legend=None),
            tooltip=[
                alt.Tooltip("yearmonth(order_purchase_timestamp):T", title="Month"),
                alt.Tooltip("sum(order_value):Q", title="Revenue", format=",.0f"),
            ],
        )
        .transform_filter(state_sel)
        .properties(height=140, title="Revenue over time ")
    )

    cat_bar = (
        alt.Chart(base)
        .mark_bar()
        .encode(
            y=alt.Y("top_category:N", sort="-x", title="Category"),
            x=alt.X("sum(order_value):Q", title="Revenue (BRL)"),
            color=alt.Color("top_category:N", legend=None),
            tooltip=[
                alt.Tooltip("top_category:N", title="Category"),
                alt.Tooltip("sum(order_value):Q", title="Revenue", format=",.0f"),
            ],
        )
        .transform_filter(state_sel)
        .transform_window(rank="rank(sum(order_value))")
        .transform_filter(alt.datum.rank <= 10)
        .properties(height=140, title="Top categories")
    )

    chart = alt.vconcat(
        bar_states,
        line_month,
        cat_bar,
        spacing=6,
    ).resolve_scale(color="independent")

    return chart
