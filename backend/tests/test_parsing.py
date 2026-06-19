import asyncio
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
import pytest

from app.services.parsing import MAX_FILE_SIZE_BYTES, read_uploaded_csv


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
