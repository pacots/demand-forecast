import asyncio
from io import BytesIO

from fastapi import HTTPException, UploadFile
import pytest

from app.routers.forecast import forecast


def test_forecast_route_returns_products_and_excluded_products() -> None:
    csv_content = (
        b"date,product_id,quantity_sold\n"
        b"2026-01-05,SKU-1,10\n"
        b"2026-01-12,SKU-1,10\n"
        b"2026-01-19,SKU-1,10\n"
        b"2026-01-26,SKU-1,10\n"
        b"2026-02-02,SKU-1,10\n"
        b"2026-02-09,SKU-1,10\n"
        b"2026-02-16,SKU-1,10\n"
        b"2026-02-23,SKU-1,10\n"
        b"2026-01-05,SKU-2,4\n"
        b"2026-01-12,SKU-2,5\n"
    )

    response = asyncio.run(forecast(make_upload(csv_content)))
    body = response.model_dump(mode="json")

    assert body["excluded_products"] == [
        {
            "product_id": "SKU-2",
            "reason": "Insufficient history: fewer than 8 weeks.",
        }
    ]
    assert len(body["products"]) == 1

    product = body["products"][0]
    assert product["product_id"] == "SKU-1"
    assert product["reorder_soon"] is False
    assert len(product["historical_series"]) == 8
    assert product["historical_series"][0] == {
        "date": "2026-01-05",
        "quantity_sold": 10.0,
    }
    assert len(product["forecast_series"]) == 4
    assert product["forecast_series"][0] == {
        "date": "2026-03-02",
        "forecasted_quantity": 10.0,
    }


def test_forecast_route_rejects_invalid_schema() -> None:
    csv_content = (
        b"sale_date,sku,units\n"
        b"2026-01-05,SKU-1,10\n"
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(forecast(make_upload(csv_content)))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "CSV file is missing required columns: date, product_id, quantity_sold."
    )


def make_upload(contents: bytes) -> UploadFile:
    return UploadFile(filename="sales.csv", file=BytesIO(contents))
