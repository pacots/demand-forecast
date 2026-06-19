from io import BytesIO

from fastapi import UploadFile


async def read_uploaded_csv(upload: UploadFile) -> BytesIO:
    """Read an uploaded CSV into a seekable, in-memory buffer."""

    contents = await upload.read()
    return BytesIO(contents)
