import pandas as pd

from app.services.forecasting import FORECAST_HORIZON_WEEKS, forecast_product


def test_forecast_product_returns_four_week_forecast() -> None:
    series = pd.Series([10, 12, 13, 15, 16, 18, 19, 21], dtype=float)

    result = forecast_product(series)

    assert len(result) == FORECAST_HORIZON_WEEKS
    assert all(isinstance(value, float) for value in result)
    assert all(value >= 0 for value in result)


def test_forecast_product_projects_upward_trend() -> None:
    series = pd.Series([5, 7, 9, 11, 13, 15, 17, 19], dtype=float)

    result = forecast_product(series)

    assert result[0] > series.iloc[-1]
    assert result[-1] > result[0]
