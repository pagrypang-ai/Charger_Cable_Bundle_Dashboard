# Charger + Cable + Bundle Dashboard Prototype

This Streamlit prototype reads one unified product table and shows charger, cable, and charger + cable bundle products through the same dashboard structure.

## Core Rules

- All products live in one Google Sheets table.
- `Product Type` is single-select, not multi-select.
- The default `Product Type` is `Charger`.
- Charger, Cable, and Charger + Cable Bundle are never shown together in the same Product Value Matrix.
- KPI, filters, and hover fields stay unified across all three product types.
- Product Value logic changes by `Product Type`, and the app shows a short note above the chart.

## Files

- `streamlit_app.py`: main Streamlit app
- `requirements.txt`: Streamlit Cloud dependencies
- `data/product_data_sample.csv`: local sample data converted from the provided workbook
- `tests/test_dashboard_logic.py`: lightweight logic tests using Python `unittest`

## Data Source

The app loads data in this order:

1. Uploaded CSV/XLSX from the sidebar
2. Google Sheets published CSV URL from Streamlit Secrets
3. Local sample CSV

For Streamlit Cloud, add this secret:

```toml
GOOGLE_SHEET_CSV_URL = "your_google_sheet_csv_export_url"
```

## Expected Columns

- `Channel`
- `Product Type`
- `Brand`
- `Model Number / Product ID`
- `Product Name`
- `URL of Image`
- `Pickup or Not`
- `Sold by`
- `Price`
- `Was Price`
- `Rating`
- `Number of Reviews`
- `Pack`
- `Bundle`
- `Connect Type/Ports`
- `Fast Charging`
- `Max Output Power`
- `Cable Length`
- `Charging Tech`
- `Warranty`
- `Link`
- date columns such as `2026-07-28`

## Deploy

Upload these files to a GitHub repository root:

- `streamlit_app.py`
- `requirements.txt`
- `README.md`
- `data/product_data_sample.csv`

In Streamlit Cloud:

- Branch: `main`
- Main file path: `streamlit_app.py`
- Secret: `GOOGLE_SHEET_CSV_URL`

