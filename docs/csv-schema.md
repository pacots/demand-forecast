# CSV Input Schema

The demand forecasting tool accepts sales-history files in comma-separated value
(CSV) format. Each row represents the quantity sold for one product on one date.
Column names are case-sensitive and must match the names below exactly.

## Required columns

| Column | Type | Rules |
| --- | --- | --- |
| `date` | Date | A valid date in one of the accepted formats below. Must not be blank. |
| `product_id` | String | A non-empty product or SKU identifier. Values are treated as text, so leading zeros are significant. |
| `quantity_sold` | Number | A finite, non-negative quantity. Whole or decimal values are accepted. Must not be blank. |

## Accepted date formats

Use one date format consistently throughout a file. The preferred format is ISO
8601 because it is not locale-dependent.

| Format | Example | Status |
| --- | --- | --- |
| `YYYY-MM-DD` | `2026-06-19` | Preferred |
| `YYYY/MM/DD` | `2026/06/19` | Accepted |
| `MM/DD/YYYY` | `06/19/2026` | Accepted |

Dates must contain a four-digit year and represent a real calendar date. Timestamps,
month names, and ambiguous day-first dates such as `19/06/2026` are not accepted.

## Optional columns

| Column | Type | Rules |
| --- | --- | --- |
| `price` | Number | Per-unit selling price for the row. When provided, it must be finite and non-negative; blank values are allowed. Currency symbols and thousands separators are not accepted. |

Additional columns may be included and are ignored by the forecasting pipeline.

## File and row rules

- Include exactly one header row.
- Encode the file as UTF-8 and separate fields with commas.
- Do not leave required values blank.
- A `product_id` and `date` pair should appear only once. Exact duplicate rows are removed during cleaning.
- Rows with invalid dates or invalid or negative `quantity_sold` values cannot be used for forecasting.
- Products need at least eight weeks of sales history after cleaning and weekly aggregation to receive a forecast.

## Example

```csv
date,product_id,quantity_sold,price
2026-06-05,SKU-001,12,19.99
2026-06-12,SKU-001,9,19.99
2026-06-05,SKU-002,4,8.50
```
