from io import BytesIO

from fastapi import HTTPException, UploadFile, status
import pandas as pd


MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


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
        return pd.read_csv(csv_buffer)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file could not be parsed.",
        ) from exc
