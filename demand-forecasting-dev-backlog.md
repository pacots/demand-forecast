# Development Backlog — Demand Forecasting MVP

All open technical decisions below are now locked so each ticket is unambiguous:

- **Aggregation period:** weekly (more stable than daily for small sellers)
- **Forecast horizon:** 4 weeks ahead
- **Minimum history required:** 8 weeks of data per product to be forecastable; otherwise excluded with a message
- **Model (v1):** Holt-Winters Exponential Smoothing (`statsmodels.tsa.holtwinters.ExponentialSmoothing`), additive trend, no seasonality component for v1 (seasonality detection is a v2 upgrade)
- **Reorder flag rule (v1):** flag a product "reorder soon" if forecasted next-week demand > 1.2× its trailing 4-week average
- **File upload limit:** 5MB per CSV
- **Repository structure:** `/backend`, `/frontend`, `/docs`, `/scripts`, and `/test-data`
- **Backend folder structure:** application code in `/backend/app/{routers, services, schemas}` and tests in `/backend/tests`
- **Frontend stack:** Vite + React, `axios` for API calls, `recharts` for charts
- **Hosting:** Render (backend), Vercel (frontend)
- **Auth/persistence:** none in v1 — fully stateless, re-upload each visit. `POST /forecast` receives the CSV directly and performs validation, aggregation, and forecasting in memory; no upload session or cleaned-data reference is stored

---

## EPIC: Data Design & Test Data

- [ ] **DATA-1**: Write a one-page schema spec at `docs/csv-schema.md`: required CSV columns (`date`, `product_id`, `quantity_sold`), accepted date formats, optional columns (`price`)
- [ ] **DATA-2**: Write a Python script (`scripts/generate_synthetic_data.py`) that outputs a CSV with 15–20 products, 2 years of weekly sales, seasonal pattern + random noise
- [ ] **DATA-3**: Run the script, save output as `test-data/synthetic_clean.csv`
- [ ] **DATA-4**: Manually create `test-data/messy_missing_dates.csv` (gaps in weekly history for some products)
- [ ] **DATA-5**: Manually create `test-data/messy_single_product.csv` (only one product, edge case)
- [ ] **DATA-6**: Manually create `test-data/messy_insufficient_history.csv` (products with <8 weeks of data)
- [ ] **DATA-7**: Manually create `test-data/invalid_schema.csv` (wrong/missing column names, to test rejection)
- [ ] **DATA-8**: Download Kaggle "Store Item Demand Forecasting Challenge" dataset, save a trimmed sample into `test-data/kaggle_sample.csv`

---

## EPIC: Backend Setup

- [ ] **BE-1**: Create Python virtual environment inside `/backend`
- [ ] **BE-2**: Create `requirements.txt` with pinned versions: `fastapi`, `uvicorn`, `pandas`, `statsmodels`, `python-multipart`, `pydantic`, `pytest`
- [ ] **BE-3**: Install dependencies into the venv, confirm with `pip freeze`
- [ ] **BE-4**: Create `/backend/app/{routers, services, schemas}` and `/backend/tests`; add empty `__init__.py` files to the Python package directories under `app`
- [ ] **BE-5**: Create `app/main.py` with a FastAPI app instance
- [ ] **BE-6**: Add `GET /health` route returning `{"status": "ok"}`
- [ ] **BE-7**: Run `uvicorn app.main:app --reload` locally, confirm `/health` responds via browser or Postman
- [ ] **BE-8**: Add CORS middleware to `main.py`, allow origin `http://localhost:5173` (frontend dev server)

---

## EPIC: Backend — CSV Input & Validation

- [ ] **BE-9**: Create `schemas/csv_schemas.py` with a Pydantic model defining the expected row shape
- [ ] **BE-10**: Add a reusable file-reading helper in `services/parsing.py` that accepts the uploaded CSV from the forecast route and processes it entirely in memory
- [ ] **BE-11**: Add file size check (reject files over 5MB) with a clear error response
- [ ] **BE-12**: Add file type check (reject non-CSV files)
- [ ] **BE-13**: Implement CSV parsing into a pandas DataFrame inside `services/parsing.py`
- [ ] **BE-14**: Implement column presence validation (required columns exist) in `services/parsing.py`
- [ ] **BE-15**: Implement date parsing with error handling for unparseable dates
- [ ] **BE-16**: Implement duplicate-row detection and removal (same product + date)
- [ ] **BE-17**: Implement negative/invalid quantity filtering (drop or flag rows with negative `quantity_sold`)
- [ ] **BE-18**: Write `backend/tests/test_parsing.py` covering: valid file, missing columns, bad dates, duplicates, negative values
- [ ] **BE-19**: Make the parsing service return the cleaned DataFrame plus a summary (row count, product count, date range) for use by the forecast pipeline

---

## EPIC: Backend — Aggregation

- [ ] **BE-20**: Create `services/aggregation.py` with a function to resample cleaned data into weekly buckets per product
- [ ] **BE-21**: Implement per-product history-length check; exclude products with <8 weeks of data, return their names in a separate "excluded" list
- [ ] **BE-22**: Write `backend/tests/test_aggregation.py` covering: standard case, product with gaps, product with insufficient history

---

## EPIC: Backend — Forecasting Engine

- [ ] **BE-23**: Create `services/forecasting.py` with a function `forecast_product(series) -> forecast_values`
- [ ] **BE-24**: Implement Holt-Winters Exponential Smoothing (additive trend, no seasonality) inside `forecast_product`
- [ ] **BE-25**: Set forecast horizon to 4 weeks ahead as a named constant (not a magic number)
- [ ] **BE-26**: Add fallback handling for products where the model fails to converge (e.g., flat series) — fall back to a simple moving-average forecast
- [ ] **BE-27**: Write `backend/tests/test_forecasting.py` with at least 3 cases: clear trend, flat/no-trend, noisy series
- [ ] **BE-28**: Create `services/reorder_logic.py` implementing the "reorder soon" rule (next-week forecast > 1.2× trailing 4-week average)
- [ ] **BE-29**: Write `backend/tests/test_reorder_logic.py` covering above-threshold, below-threshold, and boundary cases

---

## EPIC: Backend — Forecast Endpoint

- [ ] **BE-30**: Create `schemas/forecast_schemas.py` defining the response shape (per product: historical series, forecast series, reorder flag)
- [ ] **BE-31**: Create `routers/forecast.py` with `POST /forecast`, accepting the CSV directly as multipart form data via `UploadFile`
- [ ] **BE-32**: Wire the stateless route: read and validate the uploaded CSV → parse and clean it → aggregate it → forecast each eligible product → apply reorder logic → assemble the response; discard all in-memory data after the request
- [ ] **BE-33**: Add handling for the "excluded products" list from BE-21 so the response clearly separates forecastable vs excluded products
- [ ] **BE-34**: Manually test `/forecast` end-to-end with Postman by uploading `test-data/synthetic_clean.csv` directly
- [ ] **BE-35**: Manually test `/forecast` with each messy test file from the DATA epic, confirm errors/exclusions behave as expected

---

## EPIC: Frontend Setup

- [ ] **FE-1**: Scaffold project with `npm create vite@latest frontend -- --template react`
- [ ] **FE-2**: Install `axios` and `recharts`
- [ ] **FE-3**: Clean up default Vite boilerplate (remove demo content from `App.jsx`)
- [ ] **FE-4**: Create `src/api/client.js` with a configured axios instance pointing at the backend base URL (env-based, defaulting to `http://localhost:8000` for dev)
- [ ] **FE-5**: Create `.env.example` with `VITE_API_BASE_URL` placeholder

---

## EPIC: Frontend — Upload Flow

- [ ] **FE-6**: Create `components/FileUpload.jsx` with a file input (accept `.csv` only)
- [ ] **FE-7**: Store the selected browser `File` object in component state without uploading it or creating a server-side session
- [ ] **FE-8**: Add loading state while validation and forecasting are in progress
- [ ] **FE-9**: Add error display for failed uploads (bad schema, file too large, etc.), surfacing the backend's error message
- [ ] **FE-10**: On submit, send the selected CSV directly to `POST /forecast` as multipart form data and store the returned forecast result in component state

---

## EPIC: Frontend — Results Dashboard

- [ ] **FE-11**: Create `components/Dashboard.jsx` as the main results container
- [ ] **FE-12**: Pass the forecast result from the upload flow into `Dashboard` and render its loading, success, and error states
- [ ] **FE-13**: Create `components/ProductSelector.jsx` — dropdown/list of forecastable products
- [ ] **FE-14**: Create `components/ForecastChart.jsx` using `recharts` `LineChart`: historical series as solid line, forecast series as dashed line
- [ ] **FE-15**: Create `components/ReorderBadge.jsx` — visual badge/highlight when a product is flagged "reorder soon"
- [ ] **FE-16**: Create `components/ExcludedProductsList.jsx` showing which products were excluded and why (insufficient history)
- [ ] **FE-17**: Add empty state for "no file uploaded yet"
- [ ] **FE-18**: Add basic responsive layout/styling (CSS modules or plain CSS — no need for a UI library for v1)

---

## EPIC: Integration & Manual Testing

- [ ] **TEST-1**: Run backend and frontend together locally, full flow with `synthetic_clean.csv`
- [ ] **TEST-2**: Full flow with each messy test file from the DATA epic, confirm UI shows appropriate errors/exclusions (not silent failures)
- [ ] **TEST-3**: Test with `kaggle_sample.csv` to confirm the tool generalizes beyond your own synthetic data
- [ ] **TEST-4**: Recruit one outside person to use the tool with zero guidance; note every point of confusion
- [ ] **TEST-5**: Fix top 3 issues identified in TEST-4

---

## EPIC: Deployment

- [ ] **DEPLOY-1**: Create Render account, create a new Web Service pointing at `/backend`
- [ ] **DEPLOY-2**: Configure Render build/start commands (`pip install -r requirements.txt`, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
- [ ] **DEPLOY-3**: Set environment variables on Render if any are needed
- [ ] **DEPLOY-4**: Deploy backend, confirm `/health` responds on the live Render URL
- [ ] **DEPLOY-5**: Update backend CORS config to allow the (soon-to-exist) Vercel frontend domain
- [ ] **DEPLOY-6**: Create Vercel account, link the `/frontend` folder as a new project
- [ ] **DEPLOY-7**: Set `VITE_API_BASE_URL` env var on Vercel to point at the live Render backend URL
- [ ] **DEPLOY-8**: Deploy frontend, confirm full upload → forecast flow works on the public URL
- [ ] **DEPLOY-9**: (Optional) Purchase a domain and connect it to the Vercel deployment

---

## EPIC: Launch Prep

- [ ] **LAUNCH-1**: Flip GitHub repo visibility to public (per earlier decision)
- [ ] **LAUNCH-2**: Update README with final setup instructions and a live demo link
- [ ] **LAUNCH-3**: Write Show HN / Product Hunt post copy
- [ ] **LAUNCH-4**: Draft outreach message for the validation-phase email signup list
- [ ] **LAUNCH-5**: Post in target communities (r/shopify, r/ecommerce, r/smallbusiness) with the live link

---

## EPIC: Measurement

- [ ] **METRIC-1**: Set up basic analytics (e.g., Plausible or even simple server-side logging of upload counts) before launch
- [ ] **METRIC-2**: Define the kill/continue threshold in writing before launch day
- [ ] **METRIC-3**: After 3 weeks, review metrics + qualitative feedback, make the continue/shelve decision
