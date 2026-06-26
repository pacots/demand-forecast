from datetime import datetime
from io import BytesIO
import math
import re
from typing import Any

from fastapi import HTTPException, UploadFile, status
import pandas as pd


MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
REQUIRED_COLUMNS = ("date", "product_id", "quantity_sold")
ACCEPTED_DATE_FORMATS = (
    (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
    (r"\d{4}/\d{2}/\d{2}", "%Y/%m/%d"),
    (r"\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),
)


async def read_uploaded_csv(upload: UploadFile) -> BytesIO:
    """Read an uploaded CSV into a seekable, in-memory buffer."""

    if not upload.filename or not upload.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are accepted.",
        )

    contents = await upload.read(MAX_FILE_SIZE_BYTES + 1)
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="CSV file exceeds the 5 MB size limit.",
        )

    return BytesIO(contents)


async def parse_uploaded_csv(upload: UploadFile) -> pd.DataFrame:
    """Parse an uploaded CSV into a pandas DataFrame without touching disk."""

    csv_buffer = await read_uploaded_csv(upload)
    try:
        dataframe = pd.read_csv(csv_buffer)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file could not be parsed.",
        ) from exc

    validate_required_columns(dataframe)
    parse_date_column(dataframe)
    dataframe = filter_invalid_quantity_rows(dataframe)
    dataframe = remove_duplicate_rows(dataframe)
    return dataframe


def validate_required_columns(dataframe: pd.DataFrame) -> None:
    """Ensure the CSV includes every column required for forecasting."""

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "CSV file is missing required columns: "
                f"{', '.join(missing_columns)}."
            ),
        )


def parse_date_column(dataframe: pd.DataFrame) -> None:
    """Parse the required date column, rejecting unsupported date values."""

    parsed_dates: list[datetime] = []
    invalid_rows: list[str] = []

    for row_index, value in dataframe["date"].items():
        try:
            parsed_dates.append(parse_date_value(value))
        except ValueError:
            invalid_rows.append(str(row_index + 2))

    if invalid_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "CSV file contains unparseable dates in rows: "
                f"{', '.join(invalid_rows)}. Accepted formats are "
                "YYYY-MM-DD, YYYY/MM/DD, or MM/DD/YYYY."
            ),
        )

    dataframe["date"] = pd.to_datetime(parsed_dates)


def parse_date_value(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("date must be a non-empty string")

    value = value.strip()
    for pattern, date_format in ACCEPTED_DATE_FORMATS:
        if not re.fullmatch(pattern, value):
            continue
        return datetime.strptime(value, date_format)

    raise ValueError("date must use an accepted format")


def filter_invalid_quantity_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Drop rows whose quantity_sold cannot be used for forecasting."""

    quantities = pd.to_numeric(dataframe["quantity_sold"], errors="coerce")
    valid_mask = quantities.map(
        lambda quantity: math.isfinite(quantity) and quantity >= 0
    )

    cleaned_dataframe = dataframe.loc[valid_mask].copy()
    cleaned_dataframe["quantity_sold"] = quantities.loc[valid_mask]
    return cleaned_dataframe.reset_index(drop=True)


def remove_duplicate_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove later rows for the same product and normalized date."""

    return dataframe.drop_duplicates(
        subset=["product_id", "date"],
        keep="first",
    ).reset_index(drop=True)
