import pandas as pd
import pytest

from app.services import forecasting
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


def test_forecast_product_uses_moving_average_for_flat_series() -> None:
    series = pd.Series([8, 8, 8, 8, 8, 8, 8, 8], dtype=float)

    result = forecast_product(series)

    assert result == [8.0, 8.0, 8.0, 8.0]


def test_forecast_product_falls_back_to_moving_average_when_model_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingExponentialSmoothing:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def fit(self, optimized: bool) -> object:
            raise ValueError("model failed to converge")

    monkeypatch.setattr(
        forecasting,
        "ExponentialSmoothing",
        FailingExponentialSmoothing,
    )
    series = pd.Series([2, 4, 6, 8, 10, 12, 14, 16], dtype=float)

    result = forecast_product(series)

    assert result == [13.0, 13.0, 13.0, 13.0]
