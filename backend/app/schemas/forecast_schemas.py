from datetime import date

from pydantic import BaseModel, ConfigDict


class HistoricalPoint(BaseModel):
    date: date
    quantity_sold: float


class ForecastPoint(BaseModel):
    date: date
    forecasted_quantity: float


class ProductForecast(BaseModel):
    product_id: str
    historical_series: list[HistoricalPoint]
    forecast_series: list[ForecastPoint]
    reorder_soon: bool


class ExcludedProduct(BaseModel):
    product_id: str
    reason: str


class ForecastResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products: list[ProductForecast]
    excluded_products: list[ExcludedProduct]
