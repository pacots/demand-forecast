import pandas as pd
from fastapi import APIRouter, File, UploadFile

from app.schemas.forecast_schemas import (
    ExcludedProduct,
    ForecastPoint,
    ForecastResponse,
    HistoricalPoint,
    ProductForecast,
)
from app.services.aggregation import (
    MIN_HISTORY_WEEKS,
    WEEKLY_FREQUENCY,
    aggregate_weekly_sales,
)
from app.services.forecasting import forecast_product
from app.services.parsing import parse_uploaded_csv
from app.services.reorder_logic import should_reorder_soon


router = APIRouter(tags=["forecast"])


@router.post("/forecast", response_model=ForecastResponse)
async def forecast(file: UploadFile = File(...)) -> ForecastResponse:
    parsed_csv = await parse_uploaded_csv(file)
    weekly_aggregation = aggregate_weekly_sales(parsed_csv.dataframe)

    products = [
        build_product_forecast(product_id, product_sales)
        for product_id, product_sales in weekly_aggregation.dataframe.groupby(
            "product_id",
            sort=True,
        )
    ]
    excluded_products = [
        ExcludedProduct(
            product_id=str(product_id),
            reason=f"Insufficient history: fewer than {MIN_HISTORY_WEEKS} weeks.",
        )
        for product_id in weekly_aggregation.excluded_products
    ]

    return ForecastResponse(
        products=products,
        excluded_products=excluded_products,
    )


def build_product_forecast(
    product_id: str,
    product_sales: pd.DataFrame,
) -> ProductForecast:
    product_sales = product_sales.sort_values("week_start").reset_index(drop=True)
    historical_quantities = product_sales["quantity_sold"]
    forecast_values = forecast_product(historical_quantities)

    return ProductForecast(
        product_id=str(product_id),
        historical_series=build_historical_series(product_sales),
        forecast_series=build_forecast_series(product_sales, forecast_values),
        reorder_soon=should_reorder_soon(historical_quantities, forecast_values),
    )


def build_historical_series(product_sales: pd.DataFrame) -> list[HistoricalPoint]:
    return [
        HistoricalPoint(
            date=row.week_start.date(),
            quantity_sold=float(row.quantity_sold),
        )
        for row in product_sales.itertuples(index=False)
    ]


def build_forecast_series(
    product_sales: pd.DataFrame,
    forecast_values: list[float],
) -> list[ForecastPoint]:
    last_week_start = product_sales["week_start"].max()
    forecast_dates = pd.date_range(
        start=last_week_start + pd.Timedelta(days=7),
        periods=len(forecast_values),
        freq=WEEKLY_FREQUENCY,
    )

    return [
        ForecastPoint(
            date=forecast_date.date(),
            forecasted_quantity=forecast_value,
        )
        for forecast_date, forecast_value in zip(forecast_dates, forecast_values)
    ]
