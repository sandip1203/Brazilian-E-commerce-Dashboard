import pandas as pd
import plotly.express as px


def order_map_chart(df: pd.DataFrame):
    geo_cols = ["geolocation_lat", "geolocation_lng", "customer_city", "customer_state", "order_value"]
    geo_df = df.dropna(subset=["geolocation_lat", "geolocation_lng"])[geo_cols]

    if len(geo_df) > 5000:
        geo_df = geo_df.sample(5000, random_state=42)

    if geo_df.empty:
        return None

    fig = px.scatter_mapbox(
        geo_df,
        lat="geolocation_lat",
        lon="geolocation_lng",
        color="customer_state",
        size="order_value",
        size_max=12,
        zoom=3,
        mapbox_style="carto-positron",
        hover_data={"customer_city": True, "order_value": ":,.0f", "geolocation_lat": False, "geolocation_lng": False},
        title="Customer Order Density Map",
        height=400,
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=12, b=0)
    )

    return fig
