"""Generate reproducible weekly sales data for local development and testing."""

from __future__ import annotations

import argparse
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path


DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "test-data" / "synthetic_clean.csv"
DEFAULT_START_DATE = date(2024, 1, 7)
WEEKS = 104


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate two years of synthetic weekly product sales."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"CSV destination (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--products",
        type=int,
        choices=range(15, 21),
        default=18,
        metavar="15-20",
        help="number of products to generate (default: 18)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed for reproducible output (default: 42)",
    )
    return parser.parse_args()


def generate_rows(product_count: int, seed: int) -> list[dict[str, str | int]]:
    rng = random.Random(seed)
    rows: list[dict[str, str | int]] = []

    for product_number in range(1, product_count + 1):
        product_id = f"SKU-{product_number:03d}"
        baseline = rng.uniform(18, 120)
        seasonal_strength = rng.uniform(0.12, 0.38)
        seasonal_phase = rng.uniform(0, 2 * math.pi)
        weekly_noise = max(2.0, baseline * rng.uniform(0.06, 0.16))
        trend_per_week = rng.uniform(-0.04, 0.18)
        price = rng.uniform(6, 95)

        for week in range(WEEKS):
            sales_date = DEFAULT_START_DATE + timedelta(weeks=week)
            annual_seasonality = (
                baseline
                * seasonal_strength
                * math.sin((2 * math.pi * week / 52) + seasonal_phase)
            )
            holiday_lift = baseline * 0.25 if week % 52 in range(45, 51) else 0
            quantity = round(
                baseline
                + (trend_per_week * week)
                + annual_seasonality
                + holiday_lift
                + rng.gauss(0, weekly_noise)
            )

            rows.append(
                {
                    "date": sales_date.isoformat(),
                    "product_id": product_id,
                    "quantity_sold": max(0, quantity),
                    "price": f"{price:.2f}",
                }
            )

    return rows


def write_csv(output_path: Path, rows: list[dict[str, str | int]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["date", "product_id", "quantity_sold", "price"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    rows = generate_rows(args.products, args.seed)
    write_csv(args.output, rows)
    print(
        f"Wrote {len(rows):,} rows for {args.products} products "
        f"across {WEEKS} weeks to {args.output.resolve()}"
    )


if __name__ == "__main__":
    main()
