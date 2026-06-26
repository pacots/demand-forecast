import asyncio
from datetime import date
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
import pandas as pd
import pytest

from app.services.parsing import (
    MAX_FILE_SIZE_BYTES,
    parse_uploaded_csv,
    read_uploaded_csv,
)


def make_upload(contents: bytes, filename: str = "sales.csv") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(contents))


def test_read_uploaded_csv_accepts_file_at_size_limit() -> None:
    contents = b"a" * MAX_FILE_SIZE_BYTES

    result = asyncio.run(read_uploaded_csv(make_upload(contents)))

    assert result.read() == contents


def test_read_uploaded_csv_rejects_file_over_size_limit() -> None:
    upload = make_upload(b"a" * (MAX_FILE_SIZE_BYTES + 1))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(read_uploaded_csv(upload))

    assert exc_info.value.status_code == status.HTTP_413_CONTENT_TOO_LARGE
    assert exc_info.value.detail == "CSV file exceeds the 5 MB size limit."


def test_read_uploaded_csv_accepts_uppercase_csv_extension() -> None:
    result = asyncio.run(read_uploaded_csv(make_upload(b"data", "sales.CSV")))

    assert result.read() == b"data"


@pytest.mark.parametrize("filename", ["sales.txt", "sales.csv.exe", "sales"])
def test_read_uploaded_csv_rejects_non_csv_file(filename: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(read_uploaded_csv(make_upload(b"data", filename)))

    assert exc_info.value.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert exc_info.value.detail == "Only CSV files are accepted."


def test_parse_uploaded_csv_returns_cleaned_dataframe_and_summary() -> None:
    upload = make_upload(
        b"date,product_id,quantity_sold,price\n"
        b"2026-01-01,SKU-1,5,12.50\n"
        b"2026-01-02,SKU-2,7,9.99\n"
    )

    parsed = asyncio.run(parse_uploaded_csv(upload))
    result = parsed.dataframe

    assert list(result.columns) == ["date", "product_id", "quantity_sold", "price"]
    assert parsed.summary.row_count == 2
    assert parsed.summary.product_count == 2
    assert parsed.summary.date_range == (date(2026, 1, 1), date(2026, 1, 2))
    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-02",
    ]
    assert result.to_dict("records") == [
        {
            "date": result.loc[0, "date"],
            "product_id": "SKU-1",
            "quantity_sold": 5,
            "price": 12.50,
        },
        {
            "date": result.loc[1, "date"],
            "product_id": "SKU-2",
            "quantity_sold": 7,
            "price": 9.99,
        },
    ]


def test_parse_uploaded_csv_rejects_empty_csv() -> None:
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(parse_uploaded_csv(make_upload(b"")))

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "CSV file could not be parsed."


def test_parse_uploaded_csv_rejects_missing_required_columns() -> None:
    upload = make_upload(
        b"date,product_id,price\n"
        b"2026-01-01,SKU-1,12.50\n"
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(parse_uploaded_csv(upload))

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        exc_info.value.detail
        == "CSV file is missing required columns: quantity_sold."
    )


def test_parse_uploaded_csv_accepts_supported_date_formats() -> None:
    upload = make_upload(
        b"date,product_id,quantity_sold\n"
        b"2026/01/01,SKU-1,5\n"
        b"01/02/2026,SKU-1,7\n"
    )

    result = asyncio.run(parse_uploaded_csv(upload)).dataframe

    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-02",
    ]


@pytest.mark.parametrize(
    "date_value",
    ["2026-01-01 00:00:00", "January 1 2026", "19/06/2026", ""],
)
def test_parse_uploaded_csv_rejects_unparseable_dates(date_value: str) -> None:
    upload = make_upload(
        f"date,product_id,quantity_sold\n{date_value},SKU-1,5\n".encode()
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(parse_uploaded_csv(upload))

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == (
        "CSV file contains unparseable dates in rows: 2. Accepted formats are "
        "YYYY-MM-DD, YYYY/MM/DD, or MM/DD/YYYY."
    )


def test_parse_uploaded_csv_removes_duplicate_product_date_rows() -> None:
    upload = make_upload(
        b"date,product_id,quantity_sold\n"
        b"2026-01-01,SKU-1,5\n"
        b"2026/01/01,SKU-1,99\n"
        b"2026-01-01,SKU-2,8\n"
        b"2026-01-02,SKU-1,7\n"
    )

    result = asyncio.run(parse_uploaded_csv(upload)).dataframe

    assert result.index.tolist() == [0, 1, 2]
    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-01",
        "2026-01-02",
    ]
    assert result[["product_id", "quantity_sold"]].to_dict("records") == [
        {"product_id": "SKU-1", "quantity_sold": 5},
        {"product_id": "SKU-2", "quantity_sold": 8},
        {"product_id": "SKU-1", "quantity_sold": 7},
    ]


def test_parse_uploaded_csv_filters_invalid_quantity_rows() -> None:
    upload = make_upload(
        b"date,product_id,quantity_sold\n"
        b"2026-01-01,SKU-1,5.5\n"
        b"2026-01-02,SKU-2,-1\n"
        b"2026-01-03,SKU-3,not-a-number\n"
        b"2026-01-04,SKU-4,\n"
        b"2026-01-05,SKU-5,inf\n"
        b"2026-01-06,SKU-6,0\n"
    )

    parsed = asyncio.run(parse_uploaded_csv(upload))
    result = parsed.dataframe

    assert result[["product_id", "quantity_sold"]].to_dict("records") == [
        {"product_id": "SKU-1", "quantity_sold": 5.5},
        {"product_id": "SKU-6", "quantity_sold": 0.0},
    ]
    assert parsed.summary.row_count == 2
    assert parsed.summary.product_count == 2
    assert parsed.summary.date_range == (date(2026, 1, 1), date(2026, 1, 6))
    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-06",
    ]


def test_parse_uploaded_csv_filters_invalid_rows_before_deduplicating() -> None:
    upload = make_upload(
        b"date,product_id,quantity_sold\n"
        b"2026-01-01,SKU-1,-1\n"
        b"2026/01/01,SKU-1,6\n"
    )

    result = asyncio.run(parse_uploaded_csv(upload)).dataframe

    assert result[["product_id", "quantity_sold"]].to_dict("records") == [
        {"product_id": "SKU-1", "quantity_sold": 6}
    ]
