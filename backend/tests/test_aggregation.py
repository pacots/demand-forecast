import pandas as pd

from app.services.aggregation import aggregate_weekly_sales, resample_weekly_sales


def test_resample_weekly_sales_sums_rows_by_product_and_week() -> None:
    cleaned_data = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2026-01-05",
                    "2026-01-07",
                    "2026-01-05",
                    "2026-01-12",
                ]
            ),
            "product_id": ["SKU-1", "SKU-1", "SKU-2", "SKU-1"],
            "quantity_sold": [5, 7, 3, 2],
        }
    )

    result = resample_weekly_sales(cleaned_data)

    assert result.to_dict("records") == [
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-01-05"),
            "quantity_sold": 12,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-01-12"),
            "quantity_sold": 2,
        },
        {
            "product_id": "SKU-2",
            "week_start": pd.Timestamp("2026-01-05"),
            "quantity_sold": 3,
        },
    ]


def test_resample_weekly_sales_fills_missing_weeks_per_product() -> None:
    cleaned_data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-05", "2026-01-19", "2026-01-12"]),
            "product_id": ["SKU-1", "SKU-1", "SKU-2"],
            "quantity_sold": [5, 9, 4],
        }
    )

    result = resample_weekly_sales(cleaned_data)

    assert result.to_dict("records") == [
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-01-05"),
            "quantity_sold": 5,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-01-12"),
            "quantity_sold": 0,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-01-19"),
            "quantity_sold": 9,
        },
        {
            "product_id": "SKU-2",
            "week_start": pd.Timestamp("2026-01-12"),
            "quantity_sold": 4,
        },
    ]


def test_resample_weekly_sales_returns_expected_empty_shape() -> None:
    cleaned_data = pd.DataFrame(columns=["date", "product_id", "quantity_sold"])

    result = resample_weekly_sales(cleaned_data)

    assert result.empty
    assert list(result.columns) == ["product_id", "week_start", "quantity_sold"]


def test_aggregate_weekly_sales_excludes_products_with_short_history() -> None:
    cleaned_data = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2026-01-05",
                    "2026-01-12",
                    "2026-01-19",
                    "2026-01-26",
                    "2026-02-02",
                    "2026-02-09",
                    "2026-02-16",
                    "2026-02-23",
                    "2026-01-05",
                    "2026-01-12",
                    "2026-01-19",
                ]
            ),
            "product_id": [
                "SKU-1",
                "SKU-1",
                "SKU-1",
                "SKU-1",
                "SKU-1",
                "SKU-1",
                "SKU-1",
                "SKU-1",
                "SKU-2",
                "SKU-2",
                "SKU-2",
            ],
            "quantity_sold": [5, 7, 6, 8, 9, 10, 11, 12, 3, 4, 5],
        }
    )

    result = aggregate_weekly_sales(cleaned_data)

    assert result.excluded_products == ["SKU-2"]
    assert result.dataframe["product_id"].unique().tolist() == ["SKU-1"]
    assert len(result.dataframe) == 8


def test_aggregate_weekly_sales_counts_filled_gap_weeks_as_history() -> None:
    cleaned_data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-05", "2026-02-23", "2026-01-05"]),
            "product_id": ["SKU-1", "SKU-1", "SKU-2"],
            "quantity_sold": [5, 12, 3],
        }
    )

    result = aggregate_weekly_sales(cleaned_data)

    assert result.excluded_products == ["SKU-2"]
    assert result.dataframe.to_dict("records") == [
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-01-05"),
            "quantity_sold": 5,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-01-12"),
            "quantity_sold": 0,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-01-19"),
            "quantity_sold": 0,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-01-26"),
            "quantity_sold": 0,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-02-02"),
            "quantity_sold": 0,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-02-09"),
            "quantity_sold": 0,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-02-16"),
            "quantity_sold": 0,
        },
        {
            "product_id": "SKU-1",
            "week_start": pd.Timestamp("2026-02-23"),
            "quantity_sold": 12,
        },
    ]


def test_aggregate_weekly_sales_returns_empty_result_when_no_products() -> None:
    cleaned_data = pd.DataFrame(columns=["date", "product_id", "quantity_sold"])

    result = aggregate_weekly_sales(cleaned_data)

    assert result.dataframe.empty
    assert list(result.dataframe.columns) == [
        "product_id",
        "week_start",
        "quantity_sold",
    ]
    assert result.excluded_products == []
