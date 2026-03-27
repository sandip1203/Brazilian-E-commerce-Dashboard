from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent.parent / "notebook" / "clean_data.csv"


def mode_or_nan(series: pd.Series):
    series = series.dropna()
    if len(series) == 0:
        return np.nan
    return series.mode().iloc[0]


@st.cache_data(show_spinner=False)
def load_dataset():
    """Load cleaned dataset and return order-level table."""
    raw = pd.read_csv(DATA_PATH)

    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        if col in raw.columns:
            raw[col] = pd.to_datetime(raw[col], errors="coerce")

    num_cols = [
        "payment_value",
        "price",
        "freight_value",
        "review_score",
        "geolocation_lat",
        "geolocation_lng",
        "payment_installments",
        "product_photos_qty",
        "product_description_lenght",
    ]
    for col in num_cols:
        if col in raw.columns:
            raw[col] = pd.to_numeric(raw[col], errors="coerce")

    if "order_delivered_customer_date" in raw.columns and "order_purchase_timestamp" in raw.columns:
        raw["delivery_days"] = (
            raw["order_delivered_customer_date"] - raw["order_purchase_timestamp"]
        ).dt.total_seconds() / 86400
    else:
        raw["delivery_days"] = np.nan

    if "order_delivered_customer_date" in raw.columns and "order_estimated_delivery_date" in raw.columns:
        raw["delay_days"] = (
            raw["order_delivered_customer_date"] - raw["order_estimated_delivery_date"]
        ).dt.total_seconds() / 86400
    else:
        raw["delay_days"] = np.nan

    def classify_delay(x):
        if pd.isna(x):
            return "Unknown"
        if x > 0:
            return "Late"
        return "On Time"

    def classify_delivery_bucket(x):
        if pd.isna(x):
            return np.nan
        if x < -14:
            return "Early >14d"
        if x < -7:
            return "Early 7-14d"
        if x <= 0:
            return "Early 0-7d"
        if x <= 7:
            return "Late 1-7d"
        if x <= 14:
            return "Late 8-14d"
        return "Late >14d"

    raw["delivery_status"] = raw["delay_days"].apply(classify_delay)

    value_col = "payment_value" if "payment_value" in raw.columns else None
    if value_col is None and "price" in raw.columns and "freight_value" in raw.columns:
        raw["line_value"] = raw["price"] + raw["freight_value"]
        value_col = "line_value"

    category_col = (
        "product_category_name_english"
        if "product_category_name_english" in raw.columns
        else "product_category_name"
        if "product_category_name" in raw.columns
        else None
    )

    agg_map = {
        "order_purchase_timestamp": ("order_purchase_timestamp", "min"),
        "order_approved_at": ("order_approved_at", "min"),
        "order_delivered_carrier_date": ("order_delivered_carrier_date", "min"),
        "order_delivered_customer_date": ("order_delivered_customer_date", "max"),
        "order_estimated_delivery_date": ("order_estimated_delivery_date", "max"),
        "customer_unique_id": ("customer_unique_id", mode_or_nan),
        "customer_state": ("customer_state", mode_or_nan),
        "seller_id": ("seller_id", mode_or_nan),
        "review_score": ("review_score", "mean"),
        "delay_days": ("delay_days", "mean"),
        "delivery_days": ("delivery_days", "mean"),
        "delivery_status": ("delivery_status", mode_or_nan),
        "geolocation_lat": ("geolocation_lat", "mean"),
        "geolocation_lng": ("geolocation_lng", "mean"),
        "product_photos_qty_avg": ("product_photos_qty", "mean"),
        "product_description_lenght_avg": ("product_description_lenght", "mean"),
    }

    if "payment_type" in raw.columns:
        agg_map["payment_types"] = ("payment_type", lambda x: ", ".join(pd.unique(x.dropna())))

    grouped = raw.groupby("order_id").agg(**agg_map)

    # Totals per order
    grouped["total_items"] = raw.groupby("order_id").size()
    if "price" in raw.columns:
        grouped["price_total"] = raw.groupby("order_id")["price"].sum()
        grouped["price"] = raw.groupby("order_id")["price"].mean()  # per-order avg price (used in corr)
    else:
        grouped["price_total"] = 0
        grouped["price"] = np.nan
    if "freight_value" in raw.columns:
        grouped["freight_total"] = raw.groupby("order_id")["freight_value"].sum()
        grouped["freight_value"] = raw.groupby("order_id")["freight_value"].mean()  # per-order avg freight (corr)
    else:
        grouped["freight_total"] = 0
        grouped["freight_value"] = np.nan

    if value_col:
        grouped["order_value"] = raw.groupby("order_id")[value_col].sum()
    else:
        grouped["order_value"] = 0
    # Keep payment_value in the table for correlation (sum per order)
    if "payment_value" in raw.columns:
        grouped["payment_value"] = raw.groupby("order_id")["payment_value"].sum()
    elif value_col:
        grouped["payment_value"] = grouped["order_value"]
    else:
        grouped["payment_value"] = np.nan

    if category_col:
        grouped["top_category"] = raw.groupby("order_id")[category_col].agg(mode_or_nan)
    else:
        grouped["top_category"] = np.nan

    if "customer_city" in raw.columns:
        grouped["customer_city"] = raw.groupby("order_id")["customer_city"].agg(mode_or_nan)
    else:
        grouped["customer_city"] = np.nan

    # Product weight for correlation (average per order)
    if "product_weight_g" in raw.columns:
        grouped["product_weight_g"] = raw.groupby("order_id")["product_weight_g"].mean()
    else:
        grouped["product_weight_g"] = np.nan

    # Derived ratios and stage durations
    grouped["shipping_ratio"] = grouped["freight_total"] / grouped["price_total"].replace({0: np.nan})
    grouped["approval_hours"] = (
        grouped["order_approved_at"] - grouped["order_purchase_timestamp"]
    ).dt.total_seconds() / 3600
    grouped["dispatch_hours"] = (
        grouped["order_delivered_carrier_date"] - grouped["order_approved_at"]
    ).dt.total_seconds() / 3600
    grouped["delivery_hours"] = (
        grouped["order_delivered_customer_date"] - grouped["order_delivered_carrier_date"]
    ).dt.total_seconds() / 3600
    grouped["on_time"] = grouped["order_delivered_customer_date"] <= grouped["order_estimated_delivery_date"]
    grouped["delivery_bucket"] = grouped["delay_days"].apply(classify_delivery_bucket)

    df = grouped.reset_index()
    df["purchase_date"] = df["order_purchase_timestamp"].dt.date
    df["year_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["purchase_year"] = df["order_purchase_timestamp"].dt.year

    return df


def filter_data(df: pd.DataFrame, months, states, categories, payments, review_range, statuses):
    if months:
        mask = df["year_month"].isin(months)
    else:
        mask = pd.Series(True, index=df.index)
    if states:
        mask &= df["customer_state"].isin(states)
    if categories:
        mask &= df["top_category"].isin(categories)
    if payments:
        mask &= df["payment_types"].str.contains("|".join(payments), case=False, na=False)
    if review_range:
        low, high = review_range
        mask &= df["review_score"].between(low, high)
    if statuses:
        mask &= df["delivery_status"].isin(statuses)
    return df.loc[mask].copy()
