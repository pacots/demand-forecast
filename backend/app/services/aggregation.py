import pandas as pd


WEEKLY_FREQUENCY = "7D"
WEEK_START_COLUMN = "week_start"
AGGREGATED_COLUMNS = ["product_id", WEEK_START_COLUMN, "quantity_sold"]


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
