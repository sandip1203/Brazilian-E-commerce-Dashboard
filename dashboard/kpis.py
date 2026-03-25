import html
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ACCENT = "#f59e0b"
TREND_HEIGHT = 110
CATEGORY_LABEL_SHORT_OVERRIDES = {
    "construction_tools_lights": "Tools & Lights",
}

# Regional grouping for Brazil (IBGE macroregions)
REGION_MAP = {
    "AC": "North",
    "AL": "Northeast",
    "AP": "North",
    "AM": "North",
    "BA": "Northeast",
    "CE": "Northeast",
    "DF": "Central-West",
    "ES": "Southeast",
    "GO": "Central-West",
    "MA": "Northeast",
    "MG": "Southeast",
    "MS": "Central-West",
    "MT": "Central-West",
    "PA": "North",
    "PB": "Northeast",
    "PE": "Northeast",
    "PI": "Northeast",
    "PR": "South",
    "RJ": "Southeast",
    "RN": "Northeast",
    "RO": "North",
    "RR": "North",
    "RS": "South",
    "SC": "South",
    "SE": "Northeast",
    "SP": "Southeast",
    "TO": "North",
}


def _safe_mean(series):
    series = series.dropna()
    return series.mean() if not series.empty else np.nan


def _escape_text(value) -> str:
    return html.escape("" if value is None else str(value))


def _format_category_label(category: str) -> str:
    if category is None or pd.isna(category):
        return "Unknown"
    if category in CATEGORY_LABEL_SHORT_OVERRIDES:
        return CATEGORY_LABEL_SHORT_OVERRIDES[category]
    return str(category).replace("_", " ").title()


def _latest_month_masks(df: pd.DataFrame) -> Optional[Tuple[pd.Series, pd.Series, str, str]]:
    if "order_purchase_timestamp" not in df.columns:
        return None
    months = (
        df["order_purchase_timestamp"]
        .dt.to_period("M")
        .dropna()
        .sort_values()
        .unique()
    )
    if len(months) < 2:
        return None
    current, previous = months[-1], months[-2]
    month_periods = df["order_purchase_timestamp"].dt.to_period("M")
    return (
        month_periods == current,
        month_periods == previous,
        str(current),
        str(previous),
    )


def _delta_label(delta: float, suffix: str, invert: bool = False, precision: int = 1) -> Tuple[str, str]:
    if delta is None or np.isnan(delta):
        return "—", "muted"
    arrow = "▲" if delta >= 0 else "▼"
    good = delta >= 0
    if invert:
        good = not good
    color = "good" if good else "bad"
    return f"{arrow} {delta:.{precision}f}{suffix}", color


def _sparkline(series: pd.Series, color: str) -> Optional[px.area]:
    if series is None or series.empty:
        return None
    data = series.reset_index()
    data.columns = ["period", "value"]
    fig = px.area(
        data.tail(8),
        x="period",
        y="value",
        height=TREND_HEIGHT,
    )
    fig.update_traces(line_color=color, fillcolor="rgba(245, 158, 11, 0.2)", hovertemplate="%{x}<br>%{y:,.0f}")
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _mini_bar(labels, values, color=ACCENT, fmt=".1f"):
    if not values or any(pd.isna(v) for v in values):
        return None
    fig = px.bar(
        x=labels,
        y=values,
        text=[f"{v:{fmt}}" for v in values],
        height=TREND_HEIGHT,
    )
    fig.update_traces(
        marker_color=["#cbd5e1", color],
        textposition="outside",
        cliponaxis=False,
        hovertemplate=f"%{{x}}: %{{y:{fmt}}}",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _state_bar(top_states: pd.DataFrame):
    if top_states is None or top_states.empty:
        return None
    fig = px.bar(
        top_states,
        x="ratio",
        y="customer_state",
        orientation="h",
        height=TREND_HEIGHT,
        text="ratio",
        color="ratio",
        color_continuous_scale=["#bfdbfe", "#0ea5e9"],
    )
    fig.update_traces(
        texttemplate="%{text:.0%}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}: %{x:.1%}",
    )
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _card(mark: Dict, column):
    value_html = mark.get("value_html")
    title = _escape_text(f"{mark['icon']} {mark['title']}")
    value = value_html if value_html is not None else _escape_text(mark["value"])
    delta = _escape_text(mark["delta"])
    subtitle = _escape_text(mark["subtitle"])
    column.markdown(
        f"""
        <div class="kpi2">
            <div class="kpi2__title">{title}</div>
            <div class="kpi2__main">
                <div class="kpi2__value">{value}</div>
                <div class="kpi2__delta kpi2__delta--{mark['delta_class']}">{delta}</div>
            </div>
            <div class="kpi2__sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _otd_card(df: pd.DataFrame, masks) -> Dict:
    cur_mask, prev_mask, cur_label, prev_label = masks
    cur_rate = df.loc[cur_mask, "on_time"].dropna().mean()
    prev_rate = df.loc[prev_mask, "on_time"].dropna().mean()
    delta_pp = (cur_rate - prev_rate) * 100 if not (np.isnan(cur_rate) or np.isnan(prev_rate)) else np.nan
    delta, delta_class = _delta_label(delta_pp, " pp", invert=False, precision=1)
    fig = _mini_bar([prev_label, cur_label], [prev_rate * 100, cur_rate * 100], color="#10b981", fmt=".1f")
    value = f"{cur_rate:.1%}" if not np.isnan(cur_rate) else "—"
    subtitle = f"{prev_label} {prev_rate:.1%} → {cur_label} {value}" if not np.isnan(prev_rate) and value != "—" else "Share delivered on or before ETA"
    return {
        "icon": "🚚",
        "title": "On-Time Delivery Rate (MoM)",
        "value": value,
        "delta": delta,
        "delta_class": delta_class,
        "subtitle": subtitle,
        "fig": None,
    }


def _aov_card(df: pd.DataFrame, masks) -> Dict:
    cur_mask, prev_mask, cur_label, prev_label = masks
    cur_orders = df.loc[cur_mask]
    prev_orders = df.loc[prev_mask]
    cur_aov = cur_orders["order_value"].sum() / cur_orders["order_id"].nunique() if not cur_orders.empty else np.nan
    prev_aov = prev_orders["order_value"].sum() / prev_orders["order_id"].nunique() if not prev_orders.empty else np.nan
    delta_abs = cur_aov - prev_aov if not (np.isnan(cur_aov) or np.isnan(prev_aov)) else np.nan
    delta_pct = (delta_abs / prev_aov * 100) if not (np.isnan(delta_abs) or prev_aov == 0) else np.nan
    delta, delta_class = _delta_label(delta_pct, "%", invert=False, precision=1)
    fig = None

    # New vs repeat split for current period
    cust_counts = cur_orders.groupby("customer_unique_id")["order_id"].nunique()
    cur_orders = cur_orders.assign(is_repeat=cur_orders["customer_unique_id"].map(cust_counts) > 1)
    repeat_aov = cur_orders.loc[cur_orders["is_repeat"], "order_value"].mean()
    new_aov = cur_orders.loc[~cur_orders["is_repeat"], "order_value"].mean()
    subtitle = (
        f"Repeat {repeat_aov:,.0f} vs New {new_aov:,.0f} BRL"
        if not np.isnan(repeat_aov) and not np.isnan(new_aov)
        else "Average Order Value (filtered)"
    )

    return {
        "icon": "💳",
        "title": "Average Order Value (MoM)",
        "value": f"R$ {cur_aov:,.0f}" if not np.isnan(cur_aov) else "—",
        "delta": delta,
        "delta_class": delta_class,
        "subtitle": subtitle,
        "fig": fig,
    }


def _adt_card(df: pd.DataFrame, masks) -> Dict:
    cur_mask, prev_mask, cur_label, prev_label = masks
    cur_days = _safe_mean(df.loc[cur_mask, "delivery_days"])
    prev_days = _safe_mean(df.loc[prev_mask, "delivery_days"])
    delta_days = cur_days - prev_days if not (np.isnan(cur_days) or np.isnan(prev_days)) else np.nan
    delta, delta_class = _delta_label(delta_days, " d", invert=True, precision=1)
    fig = None

    # Regional variance (current period)
    regional = (
        df.loc[cur_mask]
        .dropna(subset=["customer_state", "delivery_days"])
        .assign(region=lambda d: d["customer_state"].map(REGION_MAP))
    )
    gap_text = "Regional variance n/a"
    if not regional.empty:
        agg = regional.groupby("region")["delivery_days"].mean().dropna()
        if agg.size >= 2:
            fastest = agg.idxmin()
            slowest = agg.idxmax()
            gap = agg[slowest] - agg[fastest]
            gap_text = f"{fastest} {agg[fastest]:.1f}d vs {slowest} {agg[slowest]:.1f}d (gap {gap:.1f}d)"

    subtitle = gap_text
    return {
        "icon": "⏱️",
        "title": "Delivery Efficiency Change",
        "value": f"{cur_days:.1f} d" if not np.isnan(cur_days) else "—",
        "delta": delta,
        "delta_class": delta_class,
        "subtitle": subtitle,
        "fig": fig,
    }


def _seller_speed_card(df: pd.DataFrame, masks) -> Dict:
    cur_mask, prev_mask, cur_label, prev_label = masks
    cur_hours = _safe_mean(df.loc[cur_mask, "dispatch_hours"])
    prev_hours = _safe_mean(df.loc[prev_mask, "dispatch_hours"])
    cur_days = cur_hours / 24 if not np.isnan(cur_hours) else np.nan
    prev_days = prev_hours / 24 if not np.isnan(prev_hours) else np.nan
    delta_days = cur_days - prev_days if not (np.isnan(cur_days) or np.isnan(prev_days)) else np.nan
    delta, delta_class = _delta_label(delta_days, " d", invert=True, precision=2)
    fig = None

    # Top / bottom 10% sellers (current period)
    seller = (
        df.loc[cur_mask]
        .dropna(subset=["seller_id", "dispatch_hours"])
        .groupby("seller_id")["dispatch_hours"]
        .mean()
        .dropna()
    )
    subtitle = "Fulfillment speed by seller"
    if not seller.empty and seller.size >= 10:
        q_fast = seller.quantile(0.1)
        q_slow = seller.quantile(0.9)
        fast_avg = seller[seller <= q_fast].mean() / 24
        slow_avg = seller[seller >= q_slow].mean() / 24
        subtitle = f"Top10% {fast_avg:.1f}d vs Bottom10% {slow_avg:.1f}d"

    return {
        "icon": "🏭",
        "title": "Seller Fulfillment Speed",
        "value": f"{cur_days:.2f} d" if not np.isnan(cur_days) else "—",
        "delta": delta,
        "delta_class": delta_class,
        "subtitle": subtitle,
        "fig": fig,
    }


def _category_health_card(df: pd.DataFrame, masks) -> Dict:
    cur_mask, prev_mask, cur_label, prev_label = masks
    cur_df = df.loc[cur_mask].dropna(subset=["top_category", "review_score"])
    prev_df = df.loc[prev_mask].dropna(subset=["top_category", "review_score"])

    def _calc(frame):
        grp = frame.groupby("top_category").agg(
            review=("review_score", "mean"),
            orders=("order_id", "nunique"),
        )
        return grp[grp["orders"] >= 20].sort_values("review")

    cur = _calc(cur_df) if not cur_df.empty else pd.DataFrame()
    prev = _calc(prev_df) if not prev_df.empty else pd.DataFrame()

    if cur.empty or prev.empty:
        return {
            "icon": "⭐",
            "title": "Worst Category Review",
            "value": "—",
            "delta": "No value",
            "delta_class": "muted",
            "subtitle": "Lowest average review by category (20+ orders)",
            "fig": None,
        }

    cur_cat_name = cur.index[0]
    prev_cat_name = prev.index[0]
    cur_worst = cur.iloc[0]
    prev_worst = prev.iloc[0]
    cur_display_name = _format_category_label(cur_cat_name)
    prev_display_name = _format_category_label(prev_cat_name)

    delta, delta_class = _delta_label(cur_worst["review"] - prev_worst["review"], "", invert=False, precision=2)
    value = f"{cur_worst['review']:.2f}"
    value_html = (
        f"{_escape_text(value)}"
        f"<span class=\"kpi2__value-note\">{_escape_text(cur_display_name)}</span>"
    )
    subtitle = (
        f"{prev_label}: {prev_display_name} {prev_worst['review']:.2f} → "
        f"{cur_label}: {cur_display_name} {cur_worst['review']:.2f}"
    )

    fig = None

    return {
        "icon": "⭐",
        "title": "Worst Category Review",
        "value": value,
        "value_html": value_html,
        "delta": delta,
        "delta_class": delta_class,
        "subtitle": subtitle,
        "fig": fig,
    }


def render_kpis(df):
    if df.empty:
        st.info("No data for the current filters.")
        return

    masks = _latest_month_masks(df)
    st.markdown(
        """
        <style>
        .kpi2 { padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 10px; background: #ffffff; box-shadow: 0 2px 8px rgba(15,23,42,0.06); min-height: 120px; }
        .kpi2__title { font-size: 11px; font-weight: 700; color: #475569; letter-spacing: 0.01em; }
        .kpi2__main { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-top: 6px; }
        .kpi2__value { font-size: 22px; font-weight: 800; color: #0f172a; line-height: 1.05; min-width: 0; flex: 1; overflow-wrap: anywhere; }
        .kpi2__value-note { display: block; margin-top: 6px; font-size: 0.56em; line-height: 1.2; color: #334155; }
        .kpi2__delta { font-size: 11px; font-weight: 800; padding: 6px 10px; min-width: 54px; text-align: center; border-radius: 999px; background: #f8fbff; box-shadow: inset 0 0 0 1px rgba(15,23,42,0.05); flex-shrink: 0; }
        .kpi2__delta--good { color: #16a34a; }
        .kpi2__delta--bad { color: #dc2626; }
        .kpi2__delta--muted { color: #94a3b8; }
        .kpi2__sub { font-size: 10px; color: #64748b; margin-top: 6px; overflow-wrap: anywhere; }
        div[data-testid="stVerticalBlockBorderWrapper"] .kpi2 { margin-bottom: 4px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if not masks:
        st.info("Add at least two months in the date filter to see MoM changes.")
        return

    cards = [
        _otd_card(df, masks),
        _aov_card(df, masks),
        _adt_card(df, masks),
        _seller_speed_card(df, masks),
        _category_health_card(df, masks),
    ]

    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        _card(card, col)
