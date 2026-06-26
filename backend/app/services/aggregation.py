from dataclasses import dataclass

import pandas as pd


MIN_HISTORY_WEEKS = 8
WEEKLY_FREQUENCY = "7D"
WEEK_START_COLUMN = "week_start"
AGGREGATED_COLUMNS = ["product_id", WEEK_START_COLUMN, "quantity_sold"]


@dataclass(frozen=True)
class WeeklyAggregation:
    dataframe: pd.DataFrame
    excluded_products: list[str]


def aggregate_weekly_sales(cleaned_data: pd.DataFrame) -> WeeklyAggregation:
    """Return forecastable weekly sales and products excluded for short history."""

    weekly_sales = resample_weekly_sales(cleaned_data)
    forecastable_sales, excluded_products = exclude_short_history_products(
        weekly_sales
    )
    return WeeklyAggregation(
        dataframe=forecastable_sales,
        excluded_products=excluded_products,
    )


def resample_weekly_sales(cleaned_data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate cleaned sales rows into Monday-start weekly buckets per product."""

    if cleaned_data.empty:
        return pd.DataFrame(columns=AGGREGATED_COLUMNS)

    dataframe = cleaned_data.copy()
    dataframe[WEEK_START_COLUMN] = (
        dataframe["date"].dt.to_period("W-SUN").dt.start_time
    )

    weekly_sales = (
        dataframe.groupby(["product_id", WEEK_START_COLUMN], as_index=False)[
            "quantity_sold"
        ]
        .sum()
        .sort_values(["product_id", WEEK_START_COLUMN])
        .reset_index(drop=True)
    )

    return fill_missing_weekly_buckets(weekly_sales)


def fill_missing_weekly_buckets(weekly_sales: pd.DataFrame) -> pd.DataFrame:
    """Fill missing weeks inside each product's observed date range with zero sales."""

    product_frames: list[pd.DataFrame] = []
    for product_id, product_sales in weekly_sales.groupby("product_id", sort=True):
        week_index = pd.date_range(
            product_sales[WEEK_START_COLUMN].min(),
            product_sales[WEEK_START_COLUMN].max(),
            freq=WEEKLY_FREQUENCY,
        )

        completed_sales = (
            product_sales.set_index(WEEK_START_COLUMN)["quantity_sold"]
            .reindex(week_index, fill_value=0)
            .rename_axis(WEEK_START_COLUMN)
            .reset_index()
        )
        completed_sales["product_id"] = product_id
        product_frames.append(completed_sales[AGGREGATED_COLUMNS])

    return pd.concat(product_frames, ignore_index=True)


def exclude_short_history_products(
    weekly_sales: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    """Split weekly sales into forecastable rows and excluded product names."""

    if weekly_sales.empty:
        return weekly_sales.copy(), []

    history_lengths = weekly_sales.groupby("product_id").size()
    excluded_products = sorted(
        history_lengths[history_lengths < MIN_HISTORY_WEEKS].index.tolist()
    )

    forecastable_sales = weekly_sales[
        ~weekly_sales["product_id"].isin(excluded_products)
    ].reset_index(drop=True)

    return forecastable_sales, excluded_products
