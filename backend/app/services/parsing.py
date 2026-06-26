from io import BytesIO

from fastapi import HTTPException, UploadFile, status
import pandas as pd


MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
REQUIRED_COLUMNS = ("date", "product_id", "quantity_sold")


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
