import pandas as pd

from app.services.reorder_logic import should_reorder_soon


def test_should_reorder_soon_flags_above_threshold() -> None:
    historical_series = pd.Series([8, 9, 10, 10])
    forecast_values = [12.1, 13.0, 14.0, 15.0]

    assert should_reorder_soon(historical_series, forecast_values) is True


def test_should_reorder_soon_does_not_flag_below_threshold() -> None:
    historical_series = pd.Series([8, 9, 10, 10])
    forecast_values = [11.0, 13.0, 14.0, 15.0]

    assert should_reorder_soon(historical_series, forecast_values) is False


def test_should_reorder_soon_does_not_flag_boundary_value() -> None:
    historical_series = pd.Series([10, 10, 10, 10])
    forecast_values = [12.0, 13.0, 14.0, 15.0]

    assert should_reorder_soon(historical_series, forecast_values) is False
