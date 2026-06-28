# Demand Forecast

Micro-SaaS demand forecasting for small e-commerce sellers.

Value proposition: upload a CSV of sales history and get a 4-week demand
forecast plus a reorder warning per product.

## Project Overview

This repository is organized as a small full-stack application:

```text
demand-forecast/
  backend/        FastAPI API, forecasting pipeline, and backend tests
  frontend/       Planned Vite/React client structure
  docs/           CSV format documentation
  scripts/        Data-generation utilities
  test-data/      Clean and messy CSV files for manual and automated checks
```

The v1 app is intentionally stateless. A CSV is uploaded directly to
`POST /forecast`; the backend validates, cleans, aggregates, forecasts, and
returns the response in one request. No uploaded file or cleaned dataset is
stored.

## Backend

The backend lives in `backend/` and uses FastAPI.

```text
backend/
  app/
    main.py                 FastAPI app, CORS, health route, router setup
    routers/
      forecast.py           POST /forecast endpoint
      upload.py             Reserved for upload-related routes
    schemas/
      csv_schemas.py        Expected CSV row shape
      forecast_schemas.py   Forecast API response models
      upload_schemas.py     Reserved for upload schemas
    services/
      parsing.py            CSV upload checks, parsing, cleaning, summary
      aggregation.py        Weekly per-product aggregation and exclusions
      forecasting.py        Holt-Winters forecasting with fallback
      reorder_logic.py      Reorder warning rule
  tests/                    Unit and route-level tests
  requirements.txt          Python dependencies
```

### Backend Packages

Pinned backend dependencies are in `backend/requirements.txt`:

- `fastapi`: API framework
- `uvicorn`: local ASGI server
- `pandas`: CSV parsing, cleaning, aggregation, time-series shaping
- `statsmodels`: Holt-Winters Exponential Smoothing
- `python-multipart`: multipart CSV uploads via `UploadFile`
- `pydantic`: request/response data models
- `pytest`: automated tests

### Forecast Pipeline

The main backend flow is implemented in `backend/app/routers/forecast.py`.

1. Accept a multipart CSV upload at `POST /forecast`.
2. Parse and clean the CSV in memory via `services/parsing.py`.
3. Aggregate cleaned rows into weekly buckets via `services/aggregation.py`.
4. Exclude products with fewer than 8 weekly buckets.
5. Forecast each remaining product for 4 weeks via `services/forecasting.py`.
6. Apply the reorder rule via `services/reorder_logic.py`.
7. Return forecastable products and excluded products separately.

### CSV Parsing And Cleaning

`services/parsing.py` handles the CSV input contract:

- rejects non-CSV filenames
- rejects files over 5 MB
- parses the upload entirely in memory
- requires `date`, `product_id`, and `quantity_sold`
- accepts dates in `YYYY-MM-DD`, `YYYY/MM/DD`, or `MM/DD/YYYY`
- drops duplicate rows with the same `product_id` and normalized `date`
- drops rows with invalid, blank, negative, or non-finite `quantity_sold`
- returns the cleaned DataFrame plus a summary with row count, product count,
  and date range

The full CSV schema is documented in `docs/csv-schema.md`.

### Aggregation

`services/aggregation.py` converts cleaned sales rows into weekly demand:

- weeks start on Monday
- sales are summed per `product_id` and `week_start`
- missing weeks inside a product's observed range are filled with zero
- products with fewer than 8 weekly buckets are excluded from forecasting

The route returns excluded products separately with an insufficient-history
reason.

### Forecasting

`services/forecasting.py` forecasts one product series at a time.

The v1 model is Holt-Winters Exponential Smoothing from `statsmodels`:

- additive trend
- no seasonality
- 4-week forecast horizon

Flat series or model failures fall back to a trailing 4-week moving-average
forecast.

### Reorder Logic

`services/reorder_logic.py` implements the v1 reorder warning:

```text
reorder_soon = next_week_forecast > 1.2 * trailing_4_week_average
```

The comparison is strictly greater-than, so a forecast exactly on the boundary
is not flagged.

### API Response Shape

`schemas/forecast_schemas.py` defines the response returned by `POST /forecast`.
Each forecastable product includes:

- `product_id`
- `historical_series`
- `forecast_series`
- `reorder_soon`

Excluded products are returned separately:

- `product_id`
- `reason`

## Frontend

The `frontend/` folder contains the planned React client structure:

```text
frontend/
  .env.example
  src/
    api/client.js
    App.jsx
    App.css
    main.jsx
    components/
      FileUpload.jsx
      Dashboard.jsx
      ProductSelector.jsx
      ForecastChart.jsx
      ReorderBadge.jsx
      ExcludedProductsList.jsx
```

The intended frontend stack is Vite + React, with:

- `axios` for API calls
- `recharts` for forecast charts
- an environment variable such as `VITE_API_BASE_URL` for the backend URL

The frontend package scaffold is not fully present yet; the files currently mark
the planned component boundaries for the upload flow and results dashboard.

## Data And Test Files

`test-data/` contains CSV files used to exercise the backend:

- `synthetic_clean.csv`: clean synthetic dataset
- `messy_missing_dates.csv`: products with weekly gaps
- `messy_single_product.csv`: one-product edge case
- `messy_insufficient_history.csv`: products with fewer than 8 weeks
- `invalid_schema.csv`: wrong column names
- `kaggle_sample.csv`: trimmed external sample

`scripts/generate_synthetic_data.py` is used to generate synthetic sales data.

## Tests

Backend tests live in `backend/tests/`:

- `test_parsing.py`: CSV validation, date parsing, duplicates, invalid quantity
- `test_aggregation.py`: weekly buckets, gaps, insufficient history
- `test_forecasting.py`: forecast shape, trend behavior, fallback behavior
- `test_reorder_logic.py`: reorder threshold behavior
- `test_forecast_route.py`: route pipeline and invalid-schema response

Run the backend tests from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

## Local Development

From `backend/`, create and use a virtual environment, install requirements, and
run the API:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Health check:

```text
GET /health
```

Forecast upload:

```text
POST /forecast
multipart form-data field: file=<sales.csv>
```

## Roadmap Notes

The backend forecasting pipeline is implemented for v1. Remaining project work
is mostly around completing the frontend scaffold, wiring the browser upload
flow to `POST /forecast`, rendering charts and excluded products, full
end-to-end testing, deployment, and launch preparation.
