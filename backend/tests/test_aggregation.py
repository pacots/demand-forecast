import pandas as pd

from app.services.aggregation import resample_weekly_sales


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
