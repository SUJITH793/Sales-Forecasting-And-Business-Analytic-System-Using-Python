# Sales Forecasting & Business Analytics System

An AI-powered sales forecasting system built with **Python**, **MySQL**, and **Power BI** that uses **Facebook Prophet** for time-series prediction with trend analysis, seasonality decomposition, and confidence intervals.

---

## Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                        │
│   Power BI Dashboards  │  Plotly Interactive Charts         │
│   Excel Reports        │  KPI Dashboard (HTML)              │
├─────────────────────────────────────────────────────────────┤
│                   PROCESSING LAYER                          │
│   Data Preprocessing   │  Feature Engineering               │
│   Facebook Prophet     │  Model Evaluation (CV)             │
│   Automation Scheduler │  Excel Export Engine                │
├─────────────────────────────────────────────────────────────┤
│                      DATA LAYER                             │
│   MySQL Database       │  CSV File Storage                  │
│   Products, Customers  │  Sales Orders, Order Items         │
│   Forecasts, KPIs      │  Model Artifacts                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
sales forecasting and business analytics system/
│
├── main.py                        # Main application entry point
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
│
├── config/
│   ├── __init__.py
│   └── settings.py                # Central configuration
│
├── database/
│   ├── __init__.py
│   ├── db_schema.py               # MySQL schema creation
│   └── sample_data.py             # Synthetic data generator
│
├── data_processing/
│   ├── __init__.py
│   ├── preprocessing.py           # Data cleaning & validation
│   └── feature_engineering.py     # Feature creation pipeline
│
├── models/
│   ├── __init__.py
│   ├── forecasting_engine.py      # Prophet forecasting engine
│   └── saved_models/              # Serialized trained models
│
├── output/
│   ├── __init__.py
│   ├── excel_export.py            # Excel report generator
│   └── dashboard.py               # Plotly dashboard builder
│
├── automation/
│   ├── __init__.py
│   └── scheduler.py               # Task automation & scheduling
│
├── data/
│   ├── raw/                       # Raw generated/imported data
│   └── processed/                 # Cleaned & processed data
│
├── output/
│   ├── excel_reports/             # Generated Excel reports
│   └── dashboards/                # Generated HTML dashboards
│
└── logs/
    └── app.log                    # Application logs
```

---

## Features

### 1. Data Layer (MySQL + CSV)
- **MySQL Database** with 6 normalized tables: products, customers, sales_orders, sales_order_items, forecasts, kpi_summary
- **Synthetic Data Generator** producing realistic sales data with seasonal patterns, trends, and noise (simulating CRM/POS sources)
- **CSV Fallback** — works without MySQL for easy setup

### 2. Data Preprocessing
- Missing value treatment (drop, mean, median, interpolation)
- Outlier detection (IQR and Z-Score methods) with capping
- Data type conversion and validation
- Duplicate removal
- Data quality reporting

### 3. Feature Engineering
- **Time features**: year, month, day, day_of_week, quarter, cyclical encoding
- **Lag features**: 7, 14, 21, 28, 30, 60, 90 day lags
- **Rolling features**: moving averages, std, min, max (7/14/30/60/90 day windows)
- **Exponential moving averages**: 7, 14, 30 day spans
- **Seasonal indicators**: festive season, year-end, financial year end, back-to-school
- **Category-level aggregation** for product-specific forecasts

### 4. Forecasting Engine (Facebook Prophet)
- **Overall Sales Forecast** with trend and seasonality decomposition
- **Category-Level Forecasts** (Technology, Furniture, Office Supplies)
- **Confidence Intervals** (95% by default) for uncertainty quantification
- **Cross-Validation** with MAE, MAPE, RMSE, and coverage metrics
- **Custom Seasonalities**: weekly, yearly, monthly, festive season
- **Model Persistence**: save/load trained models

### 5. Excel Reports
- **Executive Summary** with forecast overview and accuracy metrics
- **Forecast Results** sheet with embedded line charts
- **KPI Dashboard Data** with monthly revenue, orders, profit margin, growth
- **Category Forecasts** comparison table
- **Power BI Data** sheet formatted for direct Power BI import

### 6. Interactive Dashboards (Plotly)
- Sales Forecast with Confidence Intervals
- Trend & Seasonality Decomposition
- KPI Dashboard (Revenue, Orders, Profit, Accuracy Gauge)
- Category Performance Stacked Bar Chart
- Weekly Sales Heatmap
- Combined All-in-One Dashboard

### 7. Automation
- Configurable scheduling for data refresh and model retraining
- Background scheduler with status monitoring
- Automatic Excel report and dashboard regeneration

---

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- MySQL 8.0+ (optional — system works with CSV files)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Settings
Edit `config/settings.py` to update:
- MySQL connection details (host, user, password)
- Forecast parameters (periods, confidence interval)
- Output directories

### Step 3: Run the System
```bash
# Full pipeline (recommended for first run)
python main.py

# Generate sample data only
python main.py --generate

# Setup MySQL database
python main.py --setup-db

# Run forecast on existing data
python main.py --forecast

# Regenerate dashboards
python main.py --dashboard

# Start automated scheduler
python main.py --schedule
```

---

## Output Files

After running the full pipeline, you will find:

| Output | Location | Description |
|--------|----------|-------------|
| Excel Report | `output/excel_reports/Sales_Forecast_Report_*.xlsx` | Full business report with charts |
| Forecast Chart | `output/dashboards/forecast_chart.html` | Interactive forecast visualization |
| KPI Dashboard | `output/dashboards/kpi_dashboard.html` | Key performance indicators |
| Trend Analysis | `output/dashboards/trend_decomposition.html` | Trend & seasonality breakdown |
| Category Chart | `output/dashboards/category_comparison.html` | Product category performance |
| Sales Heatmap | `output/dashboards/sales_heatmap.html` | Day × Month sales heatmap |
| Combined Dashboard | `output/dashboards/combined_dashboard.html` | All-in-one dashboard |
| Trained Model | `models/saved_models/prophet_overall.pkl` | Saved Prophet model |

---

## Power BI Integration

1. Open Power BI Desktop
2. Click **Get Data → Excel**
3. Select the generated Excel file from `output/excel_reports/`
4. Import the **"PowerBI Data"** sheet
5. Create visuals using the Actual_Sales, Predicted_Sales, Lower_Bound, Upper_Bound columns
6. Set up **scheduled refresh** by connecting to the Excel file path

---

## Key Metrics

| Metric | Description |
|--------|-------------|
| **MAE** | Mean Absolute Error — average forecast error in dollars |
| **MAPE** | Mean Absolute Percentage Error — accuracy percentage |
| **RMSE** | Root Mean Square Error — penalizes large errors |
| **Coverage** | % of actuals within confidence interval |
| **Profit Margin** | Total profit / Total revenue × 100 |

---

## Technologies Used

| Component | Technology |
|-----------|-----------|
| Language | Python 3.9+ |
| Database | MySQL 8.0 |
| Forecasting | Facebook Prophet |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly, Power BI |
| Excel Export | OpenPyXL |
| Scheduling | Schedule library |
| ML Evaluation | Scikit-learn |

---

## Expected Improvements

- **20-30% improvement** in forecast accuracy over manual Excel methods
- Automated pipeline reduces manual effort from hours to minutes
- Confidence intervals enable risk-aware decision making
- Category-level forecasts support targeted inventory management
- Interactive dashboards provide real-time business intelligence
