import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Palette tuned for contrast on a light background
COLOR_BRAND = "#4F8EF7"       # Order volume
COLOR_BRAND_DARK = "#1F3B73"
COLOR_SATISFACTION = "#FF6B6B"
COLOR_PROFIT = "#10B981"
COLOR_PROFIT_FILL = "rgba(16,185,129,0.18)"
BG_PAPER = "#f6f8fb"
BG_PLOT = "rgba(255,255,255,0.96)"

# Load the data
df = pd.read_csv('../notebook/clean_data.csv')

# Convert date columns to datetime
df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'])
df['order_estimated_delivery_date'] = pd.to_datetime(df['order_estimated_delivery_date'])

# Calculate metrics
df['delivery_delay'] = (df['order_delivered_customer_date'] - df['order_estimated_delivery_date']).dt.days
df['order_month'] = df['order_purchase_timestamp'].dt.strftime('%Y-%m')
df['profit_margin'] = ((df['payment_value'] - df['freight_value']) / df['payment_value'] * 100).fillna(0)

# Handle infinite values
df['profit_margin'] = df['profit_margin'].replace([np.inf, -np.inf], 0)

# Prepare data for the visualization
monthly_data = df.groupby('order_month').agg({
    'order_id': 'count',
    'payment_value': 'mean',
    'review_score': 'mean',
    'profit_margin': 'mean',
    'freight_value': 'mean'
}).reset_index()

# Sort by month
monthly_data = monthly_data.sort_values('order_month')

# Calculate rolling averages for smoother trends
monthly_data['review_score_smooth'] = monthly_data['review_score'].rolling(window=3, min_periods=1).mean()
monthly_data['profit_margin_smooth'] = monthly_data['profit_margin'].rolling(window=3, min_periods=1).mean()
monthly_data['order_volume_smooth'] = monthly_data['order_id'].rolling(window=3, min_periods=1).mean()
profit_min = monthly_data['profit_margin_smooth'].min()
profit_max = monthly_data['profit_margin_smooth'].max()
profit_pad = max(5, (profit_max - profit_min) * 0.1)

# Create the figure with better spacing
fig = go.Figure()

# ============================================
# PRIMARY AXIS - Order Volume (Bar Chart)
# ============================================
fig.add_trace(
    go.Bar(
        x=monthly_data['order_month'],
        y=monthly_data['order_id'],
        name='📦 Order Volume',
        marker=dict(
            color=COLOR_BRAND,
            line=dict(color=COLOR_BRAND_DARK, width=1.2),
            opacity=0.92
        ),
        text=monthly_data['order_id'],
        textposition='outside',
        textfont=dict(size=10, color=COLOR_BRAND_DARK),
        hovertemplate='<b>Month:</b> %{x}<br>' +
                      '<b>Orders:</b> %{y:,}<br>' +
                      '<b>Avg Payment:</b> R$%{customdata[0]:.2f}<br>' +
                      '<b>Avg Freight:</b> R$%{customdata[1]:.2f}<extra></extra>',
        customdata=np.column_stack((monthly_data['payment_value'], monthly_data['freight_value'])),
        width=0.65
    )
)

# 3-month smoothed volume line to make the trend clearer
fig.add_trace(
    go.Scatter(
        x=monthly_data['order_month'],
        y=monthly_data['order_volume_smooth'],
        name='📈 Order Volume (3M trend)',
        mode='lines',
        line=dict(color=COLOR_BRAND_DARK, width=3, shape='spline'),
        yaxis='y',
        hovertemplate='<b>Month:</b> %{x}<br>' +
                      '<b>3M Trend:</b> %{y:,.0f} orders<extra></extra>'
    )
)

# ============================================
# SECONDARY AXIS - Customer Satisfaction (Line with Markers)
# ============================================
fig.add_trace(
    go.Scatter(
        x=monthly_data['order_month'],
        y=monthly_data['review_score_smooth'],
        name='⭐ Customer Satisfaction (Review Score)',
        mode='lines+markers',
        line=dict(color=COLOR_SATISFACTION, width=3, shape='spline'),
        marker=dict(
            size=10,
            color=monthly_data['review_score_smooth'],
            colorscale='Reds',
            showscale=False,
            line=dict(color='white', width=2)
        ),
        yaxis='y2',
        hovertemplate='<b>Month:</b> %{x}<br>' +
                      '<b>Review Score:</b> %{y:.2f}★<br>' +
                      '<b>Actual Score:</b> %{customdata:.2f}★<extra></extra>',
        customdata=monthly_data['review_score']
    )
)

# ============================================
# TERTIARY AXIS - Profitability (Area Chart)
# ============================================
fig.add_trace(
    go.Scatter(
        x=monthly_data['order_month'],
        y=monthly_data['profit_margin_smooth'],
        name='💰 Profit Margin (%)',
        mode='lines+markers',
        line=dict(color=COLOR_PROFIT, width=3),
        marker=dict(size=7, color=COLOR_PROFIT, line=dict(color="white", width=1.5)),
        fill='tozeroy',
        fillcolor=COLOR_PROFIT_FILL,
        yaxis='y3',
        hovertemplate='<b>Month:</b> %{x}<br>' +
                      '<b>Profit Margin:</b> %{y:.1f}%<br>' +
                      '<b>Actual Margin:</b> %{customdata:.1f}%<extra></extra>',
        customdata=monthly_data['profit_margin']
    )
)

# ============================================
# ADD REFERENCE LINES
# ============================================

# Add benchmark line for good review score (4.0)
fig.add_hline(
    y=4.0, 
    line_dash="dash", 
    line_color="#FF6B6B", 
    opacity=0.5,
    annotation_text="Good Satisfaction (4.0★)",
    annotation_position="top right",
    annotation_font_size=9,
    row=None, col=None,
    layer="above"
)

# Add benchmark line for profit margin (20%)
fig.add_hline(
    y=20, 
    line_dash="dash", 
    line_color=COLOR_PROFIT, 
    opacity=0.5,
    annotation_text="Target Profit (20%)",
    annotation_position="bottom right",
    annotation_font_size=9,
    row=None, col=None,
    layer="above"
)

# Zero baseline for profit margin so negative months stay visible
fig.add_hline(
    y=0,
    line_dash="dot",
    line_color="rgba(0,0,0,0.35)",
    opacity=0.5,
    annotation_text="Break-even (0%)",
    annotation_position="bottom left",
    annotation_font_size=9,
    row=None, col=None,
    layer="below"
)

# ============================================
# ADD KEY INSIGHTS AS ANNOTATIONS
# ============================================

# Find best and worst performing months
best_month = monthly_data.loc[monthly_data['review_score_smooth'].idxmax()]
peak_orders = monthly_data.loc[monthly_data['order_id'].idxmax()]

# Add annotation for peak orders
fig.add_annotation(
    x=peak_orders['order_month'],
    y=peak_orders['order_id'],
    xref="x",
    yref="y",
    text=f"📈 Peak: {peak_orders['order_id']:,} orders",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="#2E86AB",
    ax=0,
    ay=40,
    bgcolor="rgba(46,134,171,0.9)",
    bordercolor="white",
    borderwidth=1,
    font=dict(size=9, color="white")
)

# Add correlation insight
correlation = monthly_data['review_score_smooth'].corr(monthly_data['profit_margin_smooth'])
fig.add_annotation(
    x=0.98,
    y=0.98,
    xref="paper",
    yref="paper",
    text=f"📊 Satisfaction vs Profitability<br>Correlation: r = {correlation:.3f}",
    showarrow=False,
    bgcolor="rgba(15,59,99,0.75)",
    bordercolor="rgba(255,255,255,0.85)",
    borderwidth=1,
    font=dict(size=10, color="white"),
    align="right"
)

# ============================================
# UPDATE LAYOUT WITH THREE AXES - FULL VIEW
# ============================================

fig.update_layout(
    title=dict(
        text='<b>🎯 E-Commerce Performance Dashboard</b><br>' +
             '<i>Multi-Layer Analysis: Order Volume | Customer Satisfaction | Profitability</i>',
        x=0.5,
        xanchor='center',
        font=dict(size=20, color=COLOR_BRAND_DARK, family='Manrope, Arial Black'),
        y=0.98
    ),
    autosize=True,
    hovermode='x unified',
    template='plotly_white',
    plot_bgcolor=BG_PLOT,
    paper_bgcolor=BG_PAPER,
    margin=dict(l=80, r=110, t=120, b=90),
    bargap=0.18,
    bargroupgap=0.05,
    
    # Configure three y-axes with better spacing
    yaxis=dict(
        title=dict(
            text="📦 Order Volume",
            font=dict(size=12, color=COLOR_BRAND_DARK)
        ),
        tickfont=dict(color=COLOR_BRAND_DARK, size=10),
        gridcolor='rgba(79,142,247,0.18)',
        side='left',
        title_standoff=10,
        showgrid=True,
        zeroline=False,
        range=[0, monthly_data['order_id'].max() * 1.15]
    ),
    
    yaxis2=dict(
        title=dict(
            text="⭐ Customer Satisfaction (1-5★)",
            font=dict(size=12, color=COLOR_SATISFACTION)
        ),
        tickfont=dict(color=COLOR_SATISFACTION, size=10),
        overlaying='y',
        side='right',
        range=[0, 5.5],
        tickvals=[0, 1, 2, 3, 4, 5],
        gridcolor='rgba(255,107,107,0.1)',
        position=0.88,
        title_standoff=10,
        showgrid=False
    ),
    
    yaxis3=dict(
        title=dict(
            text="💰 Profit Margin (%)",
            font=dict(size=12, color=COLOR_PROFIT)
        ),
        tickfont=dict(color=COLOR_PROFIT, size=10),
        overlaying='y',
        side='right',
        position=0.96,
        anchor='free',
        range=[profit_min - profit_pad, profit_max + profit_pad],
        ticksuffix='%',
        gridcolor='rgba(16,185,129,0.12)',
        title_standoff=10,
        showgrid=True,
        zeroline=True,
        zerolinecolor='rgba(0,0,0,0.25)',
        zerolinewidth=1
    ),
    
    xaxis=dict(
        title=dict(
            text="Month",
            font=dict(size=12, color=COLOR_BRAND_DARK)
        ),
        tickangle=45,
        tickfont=dict(size=9),
        gridcolor='rgba(15,59,99,0.08)',
        tickformat='%Y-%m',
        nticks=20
    ),
    
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
        bgcolor='rgba(255,255,255,0.9)',
        font=dict(size=11, color='#1b2a3d'),
        borderwidth=1,
        bordercolor='rgba(0,0,0,0.08)',
        itemclick="toggle",
        itemdoubleclick="toggleothers"
    ),
    
    hoverlabel=dict(
        bgcolor="rgba(0,0,0,0.75)",
        font=dict(size=11, color="white", family="Inter, Arial")
    ),
    
    # Add more space for annotations
    annotations=[
        # Performance summary box
        dict(
            x=0.02,
            y=0.98,
            xref="paper",
            yref="paper",
            text="<b>📊 PERFORMANCE SUMMARY</b><br>" +
                 f"Total Orders: {monthly_data['order_id'].sum():,}<br>" +
                 f"Avg Monthly Orders: {monthly_data['order_id'].mean():,.0f}<br>" +
                 f"Avg Satisfaction: {monthly_data['review_score'].mean():.2f}★<br>" +
                 f"Avg Profit Margin: {monthly_data['profit_margin'].mean():.1f}%<br>" +
                 f"Best Month: {monthly_data.loc[monthly_data['order_id'].idxmax(), 'order_month']}",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.96)",
            bordercolor="rgba(0,0,0,0.08)",
            borderwidth=1,
            font=dict(size=9, color=COLOR_BRAND_DARK, family="Source Code Pro, monospace"),
            align="left",
            valign="top",
            xanchor="left",
            yanchor="top"
        )
    ]
)

# Add secondary x-axis for better month display
fig.update_xaxes(
    tickangle=45,
    tickfont=dict(size=9),
    gridcolor='rgba(15,59,99,0.08)'
)

# Adjust bar width and spacing
fig.update_traces(
    selector=dict(type='bar'),
    width=0.65,
    textangle=0,
    textfont_size=10
)

# ============================================
# SAVE AND DISPLAY
# ============================================

# Save as HTML with full width and height
fig.write_html('multilayer_dashboard_full.html', 
               config={'responsive': True, 'displayModeBar': True},
               default_width='100%',
               default_height='100%',
               include_plotlyjs='cdn',
               full_html=True)

print("✅ Full-view dashboard saved as 'multilayer_dashboard_full.html'")
print("📁 File location: multilayer_dashboard_full.html")

# Display the figure
fig.show()

# ============================================
# PRINT INSIGHTS
# ============================================

print("\n" + "="*90)
print("🔍 KEY INSIGHTS FROM MULTI-LAYER ANALYSIS")
print("="*90)

print(f"\n📈 ORDER VOLUME INSIGHTS:")
print(f"   • Total orders analyzed: {monthly_data['order_id'].sum():,}")
print(f"   • Peak order month: {peak_orders['order_month']} with {peak_orders['order_id']:,} orders")
print(f"   • Average monthly orders: {monthly_data['order_id'].mean():,.0f}")

print(f"\n⭐ CUSTOMER SATISFACTION INSIGHTS:")
print(f"   • Overall average satisfaction: {monthly_data['review_score'].mean():.2f}★")
print(f"   • Best satisfaction month: {best_month['order_month']} ({best_month['review_score_smooth']:.2f}★)")
print(f"   • Satisfaction vs Profitability correlation: {correlation:.3f}")

print(f"\n💰 PROFITABILITY INSIGHTS:")
print(f"   • Average profit margin: {monthly_data['profit_margin'].mean():.1f}%")
print(f"   • Best profit month: {monthly_data.loc[monthly_data['profit_margin'].idxmax(), 'order_month']} ({monthly_data['profit_margin'].max():.1f}%)")
print(f"   • Target benchmark: 20% {'✓ Achieved' if monthly_data['profit_margin'].mean() >= 20 else '✗ Below target'}")

print("\n" + "="*90)
print("💡 INTERACTIVE FEATURES:")
print("   • Hover over any element for detailed information")
print("   • Click legend items to toggle layers on/off")
print("   • Double-click legend to isolate a single layer")
print("   • Use toolbar to zoom, pan, and download as PNG")
print("   • Color intensity shows relative performance")
print("="*90)
print("\n🎉 Open 'multilayer_dashboard_full.html' in your browser for full-screen interactive visualization!")
