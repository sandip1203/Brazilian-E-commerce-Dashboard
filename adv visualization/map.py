import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Load data
df = pd.read_csv("../notebook/clean_data.csv")
print(f"Loaded {len(df):,} rows of data")

# Ensure date column is datetime
df["order_delivered_customer_date"] = pd.to_datetime(
    df["order_delivered_customer_date"], errors="coerce"
)

# Drop rows without coordinates
df = df.dropna(subset=["geolocation_lat", "geolocation_lng"]).copy()

# City-level aggregation
city_agg = (
    df.groupby(["customer_city", "customer_state"], as_index=False)
    .agg(
        geolocation_lat=("geolocation_lat", "mean"),
        geolocation_lng=("geolocation_lng", "mean"),
        order_count=("order_id", "count"),
        avg_price=("price", "mean"),
        total_value=("price", "sum"),
        avg_review=("review_score", "mean"),
        avg_freight=("freight_value", "mean"),
        avg_weight=("product_weight_g", "mean"),
        payment_methods=(
            "payment_type",
            lambda x: ", ".join(pd.Series(x.dropna().astype(str).unique()).head(3))
        ),
        top_categories=(
            "product_category_name_english",
            lambda x: ", ".join(
                x.dropna().astype(str).value_counts().head(2).index
            )
        ),
        last_review_date=("order_delivered_customer_date", "max"),
    )
)

# Clean/fill values
city_agg["avg_review"] = city_agg["avg_review"].fillna(4.0).round(1)
city_agg["avg_price"] = city_agg["avg_price"].fillna(0)
city_agg["total_value"] = city_agg["total_value"].fillna(0)
city_agg["avg_freight"] = city_agg["avg_freight"].fillna(0)
city_agg["avg_weight"] = city_agg["avg_weight"].fillna(0)
city_agg["payment_methods"] = city_agg["payment_methods"].replace("", "N/A").fillna("N/A")
city_agg["top_categories"] = city_agg["top_categories"].replace("", "N/A").fillna("N/A")

# Marker size and color
city_agg["marker_size"] = city_agg["order_count"].apply(
    lambda x: min(30, 8 + (x ** 0.5) * 2.5)
)

city_agg["marker_color"] = city_agg["order_count"].apply(
    lambda x:
        "#DC143C" if x >= 50 else
        "#FF6B6B" if x >= 20 else
        "#FFA07A" if x >= 10 else
        "#4ECDC4" if x >= 5 else
        "#45B7D1" if x >= 2 else
        "#95E1D3"
)

# Stars
city_agg["rating_stars"] = city_agg["avg_review"].apply(
    lambda x: "★" * int(np.floor(x)) + "☆" * (5 - int(np.floor(x)))
)

# Display names
city_agg["city_display"] = city_agg["customer_city"].astype(str).str.title()

# Safe formatted date column
city_agg["last_review_date_str"] = city_agg["last_review_date"].dt.strftime("%Y-%m-%d")
city_agg["last_review_date_str"] = city_agg["last_review_date_str"].fillna("N/A")

# Custom data for hover
customdata = np.column_stack([
    city_agg["city_display"],
    city_agg["customer_state"],
    city_agg["order_count"],
    city_agg["total_value"].round(2),
    city_agg["avg_review"].round(1),
    city_agg["avg_freight"].round(2),
    city_agg["avg_weight"].round(0),
    city_agg["top_categories"],
    city_agg["payment_methods"].str.slice(0, 40),
    city_agg["last_review_date_str"],
    city_agg["rating_stars"],
])

# Summary stats
total_orders = int(city_agg["order_count"].sum())
total_revenue = float(city_agg["total_value"].sum())
avg_review = float(city_agg["avg_review"].mean())
unique_cities = len(city_agg)
top_city = city_agg.nlargest(1, "order_count").iloc[0]

# Build figure
fig = go.Figure()

fig.add_trace(go.Scattermap(
    lat=city_agg["geolocation_lat"],
    lon=city_agg["geolocation_lng"],
    mode="markers",
    marker=dict(
        size=city_agg["marker_size"],
        color=city_agg["marker_color"],
        opacity=0.85
    ),
    customdata=customdata,
    hovertemplate=(
        "<b style='font-size:15px'>🏙️ %{customdata[0]}, %{customdata[1]}</b><br>"
        "━━━━━━━━━━━━━━━━━━━━━━<br>"
        "📦 Orders: <b>%{customdata[2]:,}</b><br>"
        "💰 Revenue: <b>R$ %{customdata[3]:,.2f}</b><br>"
        "⭐ Rating: <b>%{customdata[4]}/5.0</b> %{customdata[10]}<br>"
        "🚚 Freight: <b>R$ %{customdata[5]:,.2f}</b><br>"
        "📦 Weight: <b>%{customdata[6]:,.0f}g</b><br>"
        "🏷️ Categories: <b>%{customdata[7]}</b><br>"
        "💳 Payment: <b>%{customdata[8]}</b><br>"
        "📅 Last Delivery: <b>%{customdata[9]}</b><br>"
        "━━━━━━━━━━━━━━━━━━━━━━<br>"
        "<i>Hover for details</i>"
        "<extra></extra>"
    )
))

# Layout
fig.update_layout(
    title=dict(
        text="🇧🇷 BRAZIL CUSTOMER ORDER DISTRIBUTION",
        x=0.5,
        y=0.98,
        xanchor="center",
        yanchor="top",
        font=dict(size=24, family="Arial Black", color="#1a2634")
    ),
    # Use full viewport height feel
    height=None,
    margin=dict(l=0, r=0, t=60, b=0),
    paper_bgcolor="#f5f7fa",
    plot_bgcolor="#f5f7fa",
    showlegend=False,
    hoverlabel=dict(
        bgcolor="rgba(0,0,0,0.85)",
        font_size=12,
        font_family="Segoe UI",
        font_color="white"
    ),
    map=dict(
        style="open-street-map",
        center=dict(lat=-15.5, lon=-55.0),
        zoom=3.3
    ),
    annotations=[
        dict(
            x=0.02,
            y=0.96,
            xref="paper",
            yref="paper",
            showarrow=False,
            align="left",
            text=(
                f"<b>📈 KEY INSIGHTS</b><br>"
                f"━━━━━━━━━━━━━━<br>"
                f"📍 <b>{unique_cities:,}</b> cities<br>"
                f"📦 <b>{total_orders:,}</b> orders<br>"
                f"💰 <b>R$ {total_revenue:,.2f}</b> revenue<br>"
                f"⭐ <b>{avg_review:.1f}/5</b> rating<br>"
                f"🏆 Top: <b>{top_city['city_display']}</b> ({int(top_city['order_count']):,})"
            ),
            font=dict(size=10, color="#2c3e50"),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#4ECDC4",
            borderwidth=2,
            borderpad=10
        ),
        dict(
            x=0.98,
            y=0.96,
            xref="paper",
            yref="paper",
            showarrow=False,
            align="left",
            text=(
                "<b>📍 LEGEND</b><br>"
                "━━━━━━━━<br>"
                "🔴 <b>50+ orders</b><br>"
                "🟠 <b>20-49</b><br>"
                "🟡 <b>10-19</b><br>"
                "🟢 <b>5-9</b><br>"
                "🔵 <b>2-4</b><br>"
                "🟣 <b>1 order</b>"
            ),
            font=dict(size=10, color="#2c3e50"),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#95a5a6",
            borderwidth=1,
            borderpad=8
        ),
        dict(
            x=0.5,
            y=0.02,
            xref="paper",
            yref="paper",
            showarrow=False,
            align="center",
            text=(
                f"<b>📊 {total_orders:,} ORDERS</b> &nbsp;|&nbsp; "
                f"<b>🏙️ {unique_cities:,} CITIES</b> &nbsp;|&nbsp; "
                f"<b>⭐ {avg_review:.1f}/5</b> &nbsp;|&nbsp; "
                f"<b>💰 BRL {total_revenue:,.2f}</b>"
            ),
            font=dict(size=12, color="white", family="Arial Black"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="#4ECDC4",
            borderwidth=2,
            borderpad=10
        )
    ]
)


plot_html = fig.to_html(
    full_html=False,
    include_plotlyjs="cdn",
    config={
        "displayModeBar": True,
        "displaylogo": False,
        "responsive": True
    }
)

full_screen_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brazil Orders Map</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: #f5f7fa;
            font-family: Arial, sans-serif;
        }}

        #map-container {{
            width: 100vw;
            height: 100vh;
            margin: 0;
            padding: 0;
        }}

        #map-container .plotly-graph-div {{
            width: 100vw !important;
            height: 100vh !important;
        }}
    </style>
</head>
<body>
    <div id="map-container">
        {plot_html}
    </div>
</body>
</html>
"""

output_file = "brazil_orders_map_fullscreen.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_screen_html)

print("\nMap created successfully!")
print(f"Orders: {total_orders:,}")
print(f"Cities: {unique_cities:,}")
print(f"Revenue: R$ {total_revenue:,.2f}")
print(f"File: {output_file}")