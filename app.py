"""
Sales Forecasting Web Application
===================================
Flask-based web application for interactive sales forecasting
and business analytics with live dashboards.
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
import plotly
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import (
    PROCESSED_DATA_DIR, RAW_DATA_DIR, FORECAST_CONFIG,
    DASHBOARD_CONFIG, EXCEL_OUTPUT_DIR, MODEL_DIR
)

app = Flask(__name__, template_folder='templates', static_folder='static')

# ─── Global colors ───
COLORS = DASHBOARD_CONFIG.get('color_palette',
    ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B'])


# ─── Data Loading Helpers ───
def load_daily_sales():
    path = os.path.join(PROCESSED_DATA_DIR, 'orders_cleaned.csv')
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df['order_date'] = pd.to_datetime(df['order_date'])
    daily = df.groupby('order_date').agg(
        total_sales=('total_amount', 'sum'),
        total_orders=('order_id', 'count'),
        avg_order_value=('total_amount', 'mean'),
        total_profit=('profit', 'sum'),
        avg_discount=('discount', 'mean'),
    ).reset_index().rename(columns={'order_date': 'ds'})
    daily = daily.sort_values('ds')
    return daily


def load_orders():
    path = os.path.join(PROCESSED_DATA_DIR, 'orders_cleaned.csv')
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df['order_date'] = pd.to_datetime(df['order_date'])
    return df


def load_products():
    path = os.path.join(PROCESSED_DATA_DIR, 'products_cleaned.csv')
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def load_customers():
    path = os.path.join(PROCESSED_DATA_DIR, 'customers_cleaned.csv')
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def load_order_items():
    path = os.path.join(PROCESSED_DATA_DIR, 'order_items_cleaned.csv')
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def run_forecast(daily_sales):
    """Run Prophet forecast and return results."""
    from models.forecasting_engine import SalesForecastingEngine
    engine = SalesForecastingEngine(FORECAST_CONFIG)
    engine.train_model(daily_sales, name='overall', target_col='total_sales')
    forecast = engine.generate_forecast(name='overall')
    try:
        engine.evaluate_model(name='overall')
    except:
        pass
    return forecast, engine.metrics.get('overall', {}), engine


# ─── KPI Calculations ───
def calculate_kpis(daily_sales, orders_df):
    total_revenue = daily_sales['total_sales'].sum()
    total_orders = daily_sales['total_orders'].sum()
    total_profit = daily_sales['total_profit'].sum()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    # YoY growth
    daily_sales['year'] = daily_sales['ds'].dt.year
    yearly = daily_sales.groupby('year')['total_sales'].sum()
    if len(yearly) >= 2:
        last_year = yearly.iloc[-1]
        prev_year = yearly.iloc[-2]
        yoy_growth = ((last_year - prev_year) / prev_year * 100)
    else:
        yoy_growth = 0

    # Best month
    daily_sales['month_name'] = daily_sales['ds'].dt.strftime('%B %Y')
    monthly = daily_sales.groupby('month_name')['total_sales'].sum()
    best_month = monthly.idxmax() if len(monthly) > 0 else 'N/A'

    return {
        'total_revenue': f"\u20b9{total_revenue:,.0f}",
        'total_orders': f"{int(total_orders):,}",
        'avg_order_value': f"\u20b9{avg_order_value:,.2f}",
        'total_profit': f"\u20b9{total_profit:,.0f}",
        'profit_margin': f"{profit_margin:.1f}%",
        'yoy_growth': f"{yoy_growth:+.1f}%",
        'best_month': best_month,
        'total_revenue_raw': total_revenue,
        'total_profit_raw': total_profit,
    }


# ===================================================================
#  ROUTES
# ===================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    daily_sales = load_daily_sales()
    orders_df = load_orders()

    if daily_sales is None:
        return render_template('index.html', error="No data found. Run 'python main.py --generate' first.")

    kpis = calculate_kpis(daily_sales, orders_df)
    return render_template('index.html', kpis=kpis)


@app.route('/forecast')
def forecast_page():
    """Forecast page."""
    return render_template('forecast.html')


@app.route('/analytics')
def analytics_page():
    """Analytics page."""
    return render_template('analytics.html')


@app.route('/reports')
def reports_page():
    """Reports page with downloadable Excel files."""
    excel_dir = EXCEL_OUTPUT_DIR
    reports = []
    if os.path.exists(excel_dir):
        for f in sorted(os.listdir(excel_dir), reverse=True):
            if f.endswith('.xlsx'):
                filepath = os.path.join(excel_dir, f)
                size_kb = os.path.getsize(filepath) / 1024
                reports.append({'name': f, 'size': f"{size_kb:.1f} KB",
                                'path': filepath})
    return render_template('reports.html', reports=reports)


# ===================================================================
#  API ENDPOINTS (return Plotly JSON)
# ===================================================================

@app.route('/api/forecast-chart')
def api_forecast_chart():
    """Generate and return forecast chart data."""
    daily_sales = load_daily_sales()
    if daily_sales is None:
        return jsonify({'error': 'No data'}), 404

    forecast, metrics, engine = run_forecast(daily_sales)

    fig = go.Figure()

    # Actual sales
    fig.add_trace(go.Scatter(
        x=daily_sales['ds'].dt.strftime('%Y-%m-%d').tolist(),
        y=daily_sales['total_sales'].tolist(),
        mode='lines', name='Actual Sales',
        line=dict(color=COLORS[0], width=1.5), opacity=0.8
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
        y=forecast['yhat'].tolist(),
        mode='lines', name='Predicted Sales',
        line=dict(color=COLORS[1], width=2, dash='dot')
    ))

    # Confidence interval
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast['ds'], forecast['ds'][::-1]]).dt.strftime('%Y-%m-%d').tolist(),
        y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]).tolist(),
        fill='toself', fillcolor='rgba(162, 59, 114, 0.15)',
        line=dict(color='rgba(162, 59, 114, 0)'),
        name='95% Confidence Interval'
    ))

    # Trend
    fig.add_trace(go.Scatter(
        x=forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
        y=forecast['trend'].tolist(),
        mode='lines', name='Trend',
        line=dict(color=COLORS[2], width=2), visible='legendonly'
    ))

    fig.update_layout(
        title='Sales Forecast — Historical & Predicted',
        xaxis_title='Date', yaxis_title='Sales (\u20b9)',
        template='plotly_white', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=500, margin=dict(l=60, r=30, t=60, b=50),
    )

    # Summary data
    periods = FORECAST_CONFIG['forecast_periods']
    future_data = forecast.tail(periods)
    summary = {
        'total_predicted': f"\u20b9{future_data['yhat'].sum():,.0f}",
        'avg_daily': f"\u20b9{future_data['yhat'].mean():,.0f}",
        'peak_day': future_data.loc[future_data['yhat'].idxmax(), 'ds'].strftime('%B %d, %Y'),
        'peak_sales': f"\u20b9{future_data['yhat'].max():,.0f}",
        'lower_bound': f"\u20b9{future_data['yhat_lower'].sum():,.0f}",
        'upper_bound': f"\u20b9{future_data['yhat_upper'].sum():,.0f}",
        'mape': f"{metrics.get('mape', 0):.1f}%",
        'accuracy': f"{100 - metrics.get('mape', 0):.1f}%",
        'mae': f"\u20b9{metrics.get('mae', 0):,.0f}",
        'forecast_start': future_data['ds'].iloc[0].strftime('%B %d, %Y'),
        'forecast_end': future_data['ds'].iloc[-1].strftime('%B %d, %Y'),
    }

    return jsonify({
        'chart': json.loads(plotly.io.to_json(fig)),
        'summary': summary,
    })


@app.route('/api/trend-chart')
def api_trend_chart():
    """Trend decomposition chart."""
    daily_sales = load_daily_sales()
    if daily_sales is None:
        return jsonify({'error': 'No data'}), 404

    forecast, _, _ = run_forecast(daily_sales)

    fig = make_subplots(rows=3, cols=1,
        subplot_titles=('Trend Component', 'Weekly Seasonality', 'Yearly Seasonality'),
        vertical_spacing=0.10, row_heights=[0.4, 0.3, 0.3])

    fig.add_trace(go.Scatter(
        x=forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
        y=forecast['trend'].tolist(),
        mode='lines', name='Trend', line=dict(color=COLORS[0], width=2)
    ), row=1, col=1)

    if 'weekly' in forecast.columns:
        fig.add_trace(go.Scatter(
            x=forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
            y=forecast['weekly'].tolist(),
            mode='lines', name='Weekly', line=dict(color=COLORS[1], width=1.5)
        ), row=2, col=1)

    if 'yearly' in forecast.columns:
        fig.add_trace(go.Scatter(
            x=forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
            y=forecast['yearly'].tolist(),
            mode='lines', name='Yearly', line=dict(color=COLORS[2], width=1.5)
        ), row=3, col=1)

    fig.update_layout(
        title='Trend & Seasonality Decomposition',
        template='plotly_white', height=700,
        margin=dict(l=60, r=30, t=60, b=50),
    )

    return jsonify({'chart': json.loads(plotly.io.to_json(fig))})


@app.route('/api/kpi-charts')
def api_kpi_charts():
    """KPI dashboard charts."""
    daily_sales = load_daily_sales()
    if daily_sales is None:
        return jsonify({'error': 'No data'}), 404

    charts = {}

    # 1. Monthly Revenue
    monthly = daily_sales.set_index('ds').resample('ME').agg({
        'total_sales': 'sum', 'total_orders': 'sum', 'total_profit': 'sum'
    }).reset_index()

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=monthly['ds'].dt.strftime('%b %Y').tolist(),
        y=monthly['total_sales'].tolist(),
        name='Revenue', marker_color=COLORS[0]
    ))
    fig1.update_layout(title='Monthly Revenue', template='plotly_white',
                       height=350, margin=dict(l=50, r=20, t=50, b=60),
                       xaxis_tickangle=-45)
    charts['monthly_revenue'] = json.loads(plotly.io.to_json(fig1))

    # 2. Profit Margin Trend
    monthly['profit_margin'] = (monthly['total_profit'] / monthly['total_sales'] * 100).round(1)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=monthly['ds'].dt.strftime('%b %Y').tolist(),
        y=monthly['profit_margin'].tolist(),
        mode='lines+markers', name='Profit Margin %',
        line=dict(color=COLORS[3], width=2), fill='tozeroy',
        fillcolor='rgba(199, 62, 29, 0.1)'
    ))
    fig2.update_layout(title='Profit Margin Trend (%)', template='plotly_white',
                       height=350, margin=dict(l=50, r=20, t=50, b=60),
                       xaxis_tickangle=-45)
    charts['profit_margin'] = json.loads(plotly.io.to_json(fig2))

    # 3. Orders Trend
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=monthly['ds'].dt.strftime('%b %Y').tolist(),
        y=monthly['total_orders'].tolist(),
        mode='lines+markers', name='Orders',
        line=dict(color=COLORS[2], width=2)
    ))
    fig3.update_layout(title='Monthly Orders', template='plotly_white',
                       height=350, margin=dict(l=50, r=20, t=50, b=60),
                       xaxis_tickangle=-45)
    charts['orders_trend'] = json.loads(plotly.io.to_json(fig3))

    # 4. Day of Week Distribution
    dow = daily_sales.copy()
    dow['day'] = dow['ds'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_avg = dow.groupby('day')['total_sales'].mean().reindex(day_order).reset_index()
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=dow_avg['day'].tolist(),
        y=dow_avg['total_sales'].round(0).tolist(),
        marker_color=[COLORS[i % len(COLORS)] for i in range(7)],
        name='Avg Sales'
    ))
    fig4.update_layout(title='Average Sales by Day of Week', template='plotly_white',
                       height=350, margin=dict(l=50, r=20, t=50, b=50))
    charts['day_of_week'] = json.loads(plotly.io.to_json(fig4))

    return jsonify(charts)


@app.route('/api/category-charts')
def api_category_charts():
    """Category performance charts."""
    orders = load_orders()
    items = load_order_items()
    products = load_products()

    if orders is None or items is None or products is None:
        return jsonify({'error': 'No data'}), 404

    # Merge
    merged = items.merge(products[['product_id', 'category', 'sub_category']],
                         on='product_id', how='left')
    merged = merged.merge(orders[['order_id', 'order_date']], on='order_id', how='left')
    merged['order_date'] = pd.to_datetime(merged['order_date'])

    charts = {}

    # 1. Category Revenue Pie
    cat_revenue = merged.groupby('category')['line_total'].sum().reset_index()
    fig1 = go.Figure(data=[go.Pie(
        labels=cat_revenue['category'].tolist(),
        values=cat_revenue['line_total'].round(0).tolist(),
        hole=0.4, marker_colors=COLORS[:len(cat_revenue)]
    )])
    fig1.update_layout(title='Revenue by Category', template='plotly_white',
                       height=350, margin=dict(l=30, r=30, t=50, b=30))
    charts['category_pie'] = json.loads(plotly.io.to_json(fig1))

    # 2. Monthly Category Trend (stacked bar)
    merged['month'] = merged['order_date'].dt.to_period('M').astype(str)
    cat_monthly = merged.groupby(['month', 'category'])['line_total'].sum().reset_index()
    fig2 = px.bar(cat_monthly, x='month', y='line_total', color='category',
                  barmode='stack', color_discrete_sequence=COLORS,
                  labels={'line_total': 'Sales (\u20b9)', 'month': 'Month'})
    fig2.update_layout(title='Monthly Sales by Category', template='plotly_white',
                       height=380, xaxis_tickangle=-45,
                       margin=dict(l=50, r=20, t=50, b=80),
                       legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    charts['category_monthly'] = json.loads(plotly.io.to_json(fig2))

    # 3. Top 10 Products
    prod_revenue = merged.groupby('product_id').agg(
        product_name=('product_id', 'first'),
        total_sales=('line_total', 'sum'),
        quantity_sold=('quantity', 'sum')
    ).reset_index()
    prod_revenue = prod_revenue.merge(products[['product_id', 'product_name']], on='product_id')
    prod_revenue = prod_revenue.nlargest(10, 'total_sales')

    fig3 = go.Figure(go.Bar(
        x=prod_revenue['total_sales'].round(0).tolist(),
        y=prod_revenue['product_name_y'].tolist(),
        orientation='h', marker_color=COLORS[0]
    ))
    fig3.update_layout(title='Top 10 Products by Revenue', template='plotly_white',
                       height=350, margin=dict(l=180, r=20, t=50, b=30),
                       yaxis=dict(autorange='reversed'))
    charts['top_products'] = json.loads(plotly.io.to_json(fig3))

    # 4. Customer Segment Distribution
    customers = load_customers()
    if customers is not None:
        seg = orders.merge(customers[['customer_id', 'segment', 'region']], on='customer_id')
        seg_rev = seg.groupby('segment')['total_amount'].sum().reset_index()
        fig4 = go.Figure(data=[go.Pie(
            labels=seg_rev['segment'].tolist(),
            values=seg_rev['total_amount'].round(0).tolist(),
            hole=0.4, marker_colors=COLORS[1:4]
        )])
        fig4.update_layout(title='Revenue by Customer Segment', template='plotly_white',
                           height=350, margin=dict(l=30, r=30, t=50, b=30))
        charts['segment_pie'] = json.loads(plotly.io.to_json(fig4))

        # Region chart
        reg_rev = seg.groupby('region')['total_amount'].sum().reset_index()
        fig5 = go.Figure(go.Bar(
            x=reg_rev['region'].tolist(),
            y=reg_rev['total_amount'].round(0).tolist(),
            marker_color=COLORS[:len(reg_rev)]
        ))
        fig5.update_layout(title='Revenue by Region', template='plotly_white',
                           height=350, margin=dict(l=50, r=20, t=50, b=50))
        charts['region_bar'] = json.loads(plotly.io.to_json(fig5))

    return jsonify(charts)


@app.route('/api/heatmap')
def api_heatmap():
    """Sales heatmap."""
    daily_sales = load_daily_sales()
    if daily_sales is None:
        return jsonify({'error': 'No data'}), 404

    daily_sales['month'] = daily_sales['ds'].dt.month_name()
    daily_sales['day_of_week'] = daily_sales['ds'].dt.day_name()

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']

    pivot = daily_sales.pivot_table(values='total_sales', index='day_of_week',
                                     columns='month', aggfunc='mean')
    pivot = pivot.reindex(index=[d for d in day_order if d in pivot.index],
                          columns=[m for m in month_order if m in pivot.columns])

    fig = px.imshow(pivot, labels=dict(x="Month", y="Day", color="Avg Sales (\u20b9)"),
                    color_continuous_scale='Blues', aspect='auto')
    fig.update_layout(title='Average Sales Heatmap (Day × Month)',
                      template='plotly_white', height=400,
                      margin=dict(l=100, r=30, t=50, b=50))

    return jsonify({'chart': json.loads(plotly.io.to_json(fig))})


# ===================================================================
#  RUN SERVER
# ===================================================================
if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  Sales Forecasting Web Application")
    print("  Open in browser: http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
