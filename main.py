"""
==========================================================================
  SALES FORECASTING & BUSINESS ANALYTICS SYSTEM
  Main Application Entry Point
==========================================================================
  
  An AI-powered sales forecasting system built with Python, MySQL,
  and interactive dashboards (Power BI compatible).
  
  Architecture:
    - Data Layer:        MySQL Database / CSV files
    - Processing Layer:  Python (Pandas, NumPy, Prophet)
    - Presentation Layer: Excel Reports + Plotly Dashboards + Power BI
  
  Usage:
    python main.py              (Run full pipeline)
    python main.py --generate   (Generate sample data only)
    python main.py --forecast   (Run forecast only)
    python main.py --dashboard  (Generate dashboards only)
    python main.py --schedule   (Start automation scheduler)
==========================================================================
"""

import sys
import os
import logging
import argparse
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Configuration imports
from config.settings import (
    DB_CONFIG, RAW_DATA_DIR, PROCESSED_DATA_DIR, FORECAST_CONFIG,
    EXCEL_OUTPUT_DIR, DASHBOARD_OUTPUT_DIR, DASHBOARD_CONFIG,
    PROCESSING_CONFIG, AUTOMATION_CONFIG, MODEL_DIR, LOGGING_CONFIG
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['log_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Display application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   ███████╗ █████╗ ██╗     ███████╗███████╗                  ║
    ║   ██╔════╝██╔══██╗██║     ██╔════╝██╔════╝                  ║
    ║   ███████╗███████║██║     █████╗  ███████╗                  ║
    ║   ╚════██║██╔══██║██║     ██╔══╝  ╚════██║                  ║
    ║   ███████║██║  ██║███████╗███████╗███████║                  ║
    ║   ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝                  ║
    ║                                                              ║
    ║   FORECASTING & BUSINESS ANALYTICS SYSTEM                   ║
    ║   AI-Powered Sales Prediction Engine                        ║
    ║                                                              ║
    ║   Python + MySQL + Prophet + Power BI                       ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"    Started: {datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')}")
    print(f"    Python:  {sys.version.split()[0]}")
    print(f"    Root:    {PROJECT_ROOT}")
    print()


def step1_generate_data():
    """Step 1: Generate synthetic sales data."""
    print("\n" + "=" * 60)
    print("  STEP 1: DATA GENERATION")
    print("=" * 60)

    from database.sample_data import generate_sales_data, save_data_to_csv

    products, customers, orders, items = generate_sales_data(
        n_customers=500,
        start_date='2022-01-01',
        end_date='2025-12-31',
        avg_daily_orders=15
    )

    # Save to CSV (always available)
    save_data_to_csv(products, customers, orders, items, RAW_DATA_DIR)

    # Try MySQL (optional)
    try:
        from database.db_schema import setup_database
        from database.sample_data import load_data_to_mysql
        setup_database(DB_CONFIG)
        load_data_to_mysql(DB_CONFIG, products, customers, orders, items)
    except Exception as e:
        print(f"  [INFO] MySQL not available ({e}). Using CSV files.")

    return products, customers, orders, items


def step2_preprocess_data():
    """Step 2: Data preprocessing and cleaning."""
    print("\n" + "=" * 60)
    print("  STEP 2: DATA PREPROCESSING")
    print("=" * 60)

    from data_processing.preprocessing import DataPreprocessor

    preprocessor = DataPreprocessor(PROCESSING_CONFIG)

    # Try MySQL first, fallback to CSV
    data = None
    try:
        data = preprocessor.load_from_mysql(DB_CONFIG)
    except Exception:
        pass

    if data is None:
        data = preprocessor.load_from_csv(RAW_DATA_DIR)

    # Run preprocessing pipeline
    cleaned_data = preprocessor.preprocess_pipeline(data)
    preprocessor.save_processed_data(cleaned_data, PROCESSED_DATA_DIR)

    return cleaned_data


def step3_feature_engineering(cleaned_data):
    """Step 3: Feature engineering."""
    print("\n" + "=" * 60)
    print("  STEP 3: FEATURE ENGINEERING")
    print("=" * 60)

    from data_processing.feature_engineering import FeatureEngineer

    fe = FeatureEngineer()
    engineered = fe.run_feature_engineering(cleaned_data)

    return engineered


def step4_forecasting(daily_sales, category_sales=None):
    """Step 4: Run forecasting engine."""
    print("\n" + "=" * 60)
    print("  STEP 4: SALES FORECASTING")
    print("=" * 60)

    from models.forecasting_engine import SalesForecastingEngine

    engine = SalesForecastingEngine(FORECAST_CONFIG)
    forecast_results = engine.run_full_forecast(daily_sales, category_sales)

    # Save trained model
    model_path = os.path.join(MODEL_DIR, 'prophet_overall.pkl')
    engine.save_model('overall', model_path)

    # Add category_sales to results for dashboard
    forecast_results['category_sales'] = category_sales

    return forecast_results


def step5_export_excel(forecast_results, daily_sales):
    """Step 5: Export results to Excel."""
    print("\n" + "=" * 60)
    print("  STEP 5: EXCEL REPORT EXPORT")
    print("=" * 60)

    from output.excel_export import ExcelExporter

    exporter = ExcelExporter(EXCEL_OUTPUT_DIR)
    excel_path = exporter.export_full_report(forecast_results, daily_sales)

    return excel_path


def step6_generate_dashboards(daily_sales, forecast_results):
    """Step 6: Generate interactive dashboards."""
    print("\n" + "=" * 60)
    print("  STEP 6: DASHBOARD GENERATION")
    print("=" * 60)

    from output.dashboard import AnalyticsDashboard

    dashboard = AnalyticsDashboard(DASHBOARD_CONFIG, DASHBOARD_OUTPUT_DIR)
    dashboard_files = dashboard.generate_full_dashboard(daily_sales, forecast_results)

    return dashboard_files


def run_full_pipeline():
    """Execute the complete end-to-end pipeline."""
    start_time = datetime.now()
    print_banner()

    print("  Running FULL PIPELINE...")
    print("  Steps: Data Gen → Preprocessing → Features → Forecast → Excel → Dashboard\n")

    # Step 1: Generate Data
    step1_generate_data()

    # Step 2: Preprocess
    cleaned_data = step2_preprocess_data()

    # Step 3: Feature Engineering
    engineered = step3_feature_engineering(cleaned_data)
    daily_sales = engineered['daily_sales']
    category_sales = engineered.get('category_sales')

    # Step 4: Forecasting
    forecast_results = step4_forecasting(daily_sales, category_sales)

    # Step 5: Excel Export
    excel_path = step5_export_excel(forecast_results, daily_sales)

    # Step 6: Dashboards
    dashboard_files = step6_generate_dashboards(daily_sales, forecast_results)

    # Final Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    summary = forecast_results.get('overall_summary', {})

    print("\n" + "=" * 60)
    print("  PIPELINE EXECUTION COMPLETE")
    print("=" * 60)
    print(f"""
    Execution Time:     {elapsed:.1f} seconds
    Records Processed:  {len(cleaned_data.get('orders', [])):,}
    
    Forecast Summary:
      Period:           {summary.get('forecast_start')} to {summary.get('forecast_end')}
      Predicted Sales:  ${summary.get('total_predicted_sales', 0):,.2f}
      Daily Average:    ${summary.get('avg_daily_predicted', 0):,.2f}
      MAPE Accuracy:    {100 - summary.get('mape', 0):.1f}%
    
    Output Files:
      Excel Report:     {excel_path}
      Dashboards:       {DASHBOARD_OUTPUT_DIR}
      Saved Model:      {os.path.join(MODEL_DIR, 'prophet_overall.pkl')}
      
    Power BI:
      Connect to Excel: {excel_path}
      Use sheet:        'PowerBI Data' for direct import
    """)

    return forecast_results


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Sales Forecasting & Business Analytics System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  Run the full pipeline
  python main.py --generate       Generate sample data only
  python main.py --forecast       Run forecasting only (requires data)
  python main.py --dashboard      Generate dashboards only (requires forecast)
  python main.py --schedule       Start automated scheduler
        """
    )

    parser.add_argument('--generate', action='store_true',
                        help='Generate sample data only')
    parser.add_argument('--forecast', action='store_true',
                        help='Run forecasting on existing data')
    parser.add_argument('--dashboard', action='store_true',
                        help='Regenerate dashboards')
    parser.add_argument('--schedule', action='store_true',
                        help='Start automation scheduler')
    parser.add_argument('--setup-db', action='store_true',
                        help='Setup MySQL database schema')

    args = parser.parse_args()

    # If specific flags are set, run only those steps
    if args.generate:
        print_banner()
        step1_generate_data()

    elif args.setup_db:
        print_banner()
        from database.db_schema import setup_database
        setup_database(DB_CONFIG)

    elif args.forecast:
        print_banner()
        cleaned_data = step2_preprocess_data()
        engineered = step3_feature_engineering(cleaned_data)
        step4_forecasting(engineered['daily_sales'], engineered.get('category_sales'))

    elif args.dashboard:
        print_banner()
        print("  [INFO] Regenerating dashboards from existing data...")
        cleaned_data = step2_preprocess_data()
        engineered = step3_feature_engineering(cleaned_data)
        daily_sales = engineered['daily_sales']
        forecast_results = step4_forecasting(daily_sales, engineered.get('category_sales'))
        step6_generate_dashboards(daily_sales, forecast_results)

    elif args.schedule:
        print_banner()
        from automation.scheduler import AutomationManager
        manager = AutomationManager(AUTOMATION_CONFIG)
        print("  Running initial pipeline...")
        manager.run_full_pipeline()
        print("\n  Starting scheduler (Ctrl+C to stop)...")
        manager.start_scheduler()
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            manager.stop_scheduler()
            print("\n  Scheduler stopped. Goodbye!")

    else:
        # Default: Run full pipeline
        run_full_pipeline()


if __name__ == "__main__":
    main()
