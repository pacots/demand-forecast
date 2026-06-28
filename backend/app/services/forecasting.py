import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


FORECAST_HORIZON_WEEKS = 4


def forecast_product(series: pd.Series) -> list[float]:
    """Forecast the next weekly demand values for a single product."""

    model = ExponentialSmoothing(
        series.astype(float),
        trend="add",
        seasonal=None,
        initialization_method="estimated",
    )
    fitted_model = model.fit(optimized=True)
    forecast = fitted_model.forecast(FORECAST_HORIZON_WEEKS)

    return [max(float(value), 0.0) for value in forecast]
