import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


FORECAST_HORIZON_WEEKS = 4
MOVING_AVERAGE_WINDOW_WEEKS = 4


def forecast_product(series: pd.Series) -> list[float]:
    """Forecast the next weekly demand values for a single product."""

    numeric_series = series.astype(float)
    if numeric_series.nunique() <= 1:
        return moving_average_forecast(numeric_series)

    try:
        model = ExponentialSmoothing(
            numeric_series,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        )
        fitted_model = model.fit(optimized=True)
        forecast = fitted_model.forecast(FORECAST_HORIZON_WEEKS)
    except Exception:
        return moving_average_forecast(numeric_series)

    return clamp_forecast_values(forecast)


def moving_average_forecast(series: pd.Series) -> list[float]:
    """Repeat the trailing moving average across the forecast horizon."""

    moving_average = series.tail(MOVING_AVERAGE_WINDOW_WEEKS).mean()
    return [max(float(moving_average), 0.0)] * FORECAST_HORIZON_WEEKS


def clamp_forecast_values(forecast: pd.Series) -> list[float]:
    return [max(float(value), 0.0) for value in forecast]
