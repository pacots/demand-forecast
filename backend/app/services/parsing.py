from io import BytesIO

from fastapi import HTTPException, UploadFile, status


MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


async def read_uploaded_csv(upload: UploadFile) -> BytesIO:
    """Read an uploaded CSV into a seekable, in-memory buffer."""

    contents = await upload.read(MAX_FILE_SIZE_BYTES + 1)
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="CSV file exceeds the 5 MB size limit.",
        )

    return BytesIO(contents)
