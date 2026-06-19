from datetime import date, datetime
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CsvRow(BaseModel):
    """A validated row from an uploaded sales-history CSV file."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    date: date
    product_id: str = Field(min_length=1)
    quantity_sold: float = Field(ge=0, allow_inf_nan=False)
    price: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            raise ValueError("timestamps are not accepted")
        if isinstance(value, date):
            return value
        if not isinstance(value, str) or not value.strip():
            raise ValueError("date must not be blank")

        value = value.strip()
        accepted_formats = (
            (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
            (r"\d{4}/\d{2}/\d{2}", "%Y/%m/%d"),
            (r"\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),
        )
        for pattern, date_format in accepted_formats:
            if not re.fullmatch(pattern, value):
                continue
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue

        raise ValueError("date must use YYYY-MM-DD, YYYY/MM/DD, or MM/DD/YYYY")

    @field_validator("price", mode="before")
    @classmethod
    def blank_price_is_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value
