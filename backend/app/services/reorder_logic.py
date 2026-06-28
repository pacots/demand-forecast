from collections.abc import Sequence

import pandas as pd


REORDER_THRESHOLD_MULTIPLIER = 1.2
TRAILING_AVERAGE_WEEKS = 4


def should_reorder_soon(
    historical_series: pd.Series | Sequence[float],
    forecast_values: Sequence[float],
) -> bool:
    """Return whether next week's forecast exceeds the reorder threshold."""

    if not forecast_values:
        return False

    historical_values = pd.Series(historical_series, dtype=float)
    trailing_average = historical_values.tail(TRAILING_AVERAGE_WEEKS).mean()
    next_week_forecast = float(forecast_values[0])

    return bool(next_week_forecast > REORDER_THRESHOLD_MULTIPLIER * trailing_average)
