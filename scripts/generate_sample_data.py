#!/usr/bin/env python3
"""Generate deterministic, synthetic Australian home loan demo data."""

from __future__ import annotations

import csv
import math
import random
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path


SEED = 20260827
ROWS_PER_MONTH = 20
START_MONTH = date(2025, 1, 1)
END_MONTH = date(2026, 6, 1)

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "home_loans.csv"
GROUND_TRUTH_PATH = ROOT / "evaluation" / "ground_truth.csv"

FIELDNAMES = [
    "loan_id",
    "application_date",
    "settlement_date",
    "state",
    "postcode_region",
    "property_type",
    "occupancy_type",
    "loan_purpose",
    "first_home_buyer",
    "channel",
    "loan_amount",
    "property_value",
    "deposit_amount",
    "lvr_pct",
    "interest_rate_pct",
    "term_years",
    "repayment_type",
    "monthly_repayment",
    "application_status",
    "days_to_decision",
    "credit_score_band",
    "debt_to_income_ratio",
    "arrears_days",
    "hardship_flag",
    "annual_household_income",
    "current_balance",
]


def month_range(start: date, end: date) -> list[date]:
    months = []
    current = start
    while current <= end:
        months.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months


def weighted_choice(rng: random.Random, choices: list[tuple[str, int]]) -> str:
    values, weights = zip(*choices)
    return rng.choices(values, weights=weights, k=1)[0]


def monthly_payment(principal: float, annual_rate_pct: float, term_years: int) -> float:
    monthly_rate = annual_rate_pct / 100 / 12
    periods = term_years * 12
    factor = (1 + monthly_rate) ** periods
    return principal * monthly_rate * factor / (factor - 1)


def money(value: float) -> str:
    return f"{value:.2f}"


def generate_rows() -> list[dict[str, str]]:
    rng = random.Random(SEED)
    rows: list[dict[str, str]] = []
    loan_number = 1

    state_values = [
        ("NSW", 31),
        ("VIC", 26),
        ("QLD", 19),
        ("WA", 11),
        ("SA", 7),
        ("TAS", 2),
        ("ACT", 3),
        ("NT", 1),
    ]
    state_value_multiplier = {
        "NSW": 1.22,
        "VIC": 1.12,
        "QLD": 0.94,
        "WA": 0.92,
        "SA": 0.78,
        "TAS": 0.70,
        "ACT": 1.08,
        "NT": 0.72,
    }

    for month in month_range(START_MONTH, END_MONTH):
        next_month = (
            date(month.year + 1, 1, 1)
            if month.month == 12
            else date(month.year, month.month + 1, 1)
        )
        days_in_month = (next_month - month).days

        for _ in range(ROWS_PER_MONTH):
            application_date = month + timedelta(days=rng.randrange(days_in_month))
            state = weighted_choice(rng, state_values)
            first_home_buyer = rng.random() < 0.34
            property_type = weighted_choice(
                rng,
                [("House", 58), ("Apartment", 27), ("Townhouse", 12), ("Land", 3)],
            )
            occupancy_type = weighted_choice(
                rng, [("Owner Occupied", 72), ("Investment", 28)]
            )
            loan_purpose = weighted_choice(
                rng,
                [
                    ("Purchase", 68),
                    ("Refinance", 23),
                    ("Construction", 6),
                    ("Equity Release", 3),
                ],
            )
            channel = weighted_choice(
                rng, [("Broker", 49), ("Direct", 31), ("Digital", 20)]
            )
            postcode_region = weighted_choice(
                rng, [("Metro", 68), ("Inner Regional", 22), ("Outer Regional", 10)]
            )

            base_property_value = rng.uniform(420_000, 1_180_000)
            property_value = round(
                base_property_value * state_value_multiplier[state] / 1000
            ) * 1000

            if first_home_buyer:
                lvr_pct = min(95.0, max(72.0, rng.gauss(86.5, 5.5)))
            else:
                lvr_pct = min(92.0, max(45.0, rng.gauss(73.5, 10.0)))
            if occupancy_type == "Investment":
                lvr_pct = max(50.0, lvr_pct - rng.uniform(1.0, 5.0))
            lvr_pct = round(lvr_pct, 2)

            loan_amount = round(property_value * lvr_pct / 100 / 1000) * 1000
            deposit_amount = property_value - loan_amount

            status = weighted_choice(
                rng,
                [("Active", 70), ("Approved", 10), ("Declined", 12), ("Withdrawn", 8)],
            )
            days_to_decision = max(
                1,
                round(
                    rng.gauss(
                        {"Digital": 3.8, "Direct": 6.2, "Broker": 8.1}[channel],
                        2.2,
                    )
                ),
            )

            settlement_date_value = ""
            if status == "Active":
                settlement_date_value = (
                    application_date + timedelta(days=rng.randint(18, 58))
                ).isoformat()

            interest_rate_pct = round(
                rng.uniform(5.35, 6.65)
                + (0.15 if lvr_pct >= 90 else 0)
                + (0.08 if occupancy_type == "Investment" else 0),
                3,
            )
            term_years = weighted_choice(rng, [("25", 25), ("30", 67), ("35", 8)])
            repayment_type = weighted_choice(
                rng, [("Principal and Interest", 86), ("Interest Only", 14)]
            )
            if repayment_type == "Interest Only":
                repayment = loan_amount * interest_rate_pct / 100 / 12
            else:
                repayment = monthly_payment(
                    loan_amount, interest_rate_pct, int(term_years)
                )

            debt_to_income_ratio = round(rng.uniform(2.1, 7.2), 2)
            annual_income = round(
                max(75_000, loan_amount / debt_to_income_ratio) / 100
            ) * 100
            credit_score_band = weighted_choice(
                rng,
                [
                    ("Excellent", 22),
                    ("Very Good", 34),
                    ("Good", 29),
                    ("Fair", 12),
                    ("Limited", 3),
                ],
            )

            arrears_days = 0
            hardship_flag = False
            current_balance = 0.0
            if status == "Active":
                current_balance = loan_amount * rng.uniform(0.86, 0.995)
                arrears_bucket = weighted_choice(
                    rng, [("0", 87), ("1-29", 7), ("30-59", 4), ("60+", 2)]
                )
                if arrears_bucket == "1-29":
                    arrears_days = rng.randint(1, 29)
                elif arrears_bucket == "30-59":
                    arrears_days = rng.randint(30, 59)
                elif arrears_bucket == "60+":
                    arrears_days = rng.randint(60, 105)
                hardship_flag = arrears_days > 0 and rng.random() < 0.42

            rows.append(
                {
                    "loan_id": f"HL-{loan_number:05d}",
                    "application_date": application_date.isoformat(),
                    "settlement_date": settlement_date_value,
                    "state": state,
                    "postcode_region": postcode_region,
                    "property_type": property_type,
                    "occupancy_type": occupancy_type,
                    "loan_purpose": loan_purpose,
                    "first_home_buyer": str(first_home_buyer).lower(),
                    "channel": channel,
                    "loan_amount": money(loan_amount),
                    "property_value": money(property_value),
                    "deposit_amount": money(deposit_amount),
                    "lvr_pct": f"{lvr_pct:.2f}",
                    "interest_rate_pct": f"{interest_rate_pct:.3f}",
                    "term_years": term_years,
                    "repayment_type": repayment_type,
                    "monthly_repayment": money(repayment),
                    "application_status": status,
                    "days_to_decision": str(days_to_decision),
                    "credit_score_band": credit_score_band,
                    "debt_to_income_ratio": f"{debt_to_income_ratio:.2f}",
                    "arrears_days": str(arrears_days),
                    "hardship_flag": str(hardship_flag).lower(),
                    "annual_household_income": money(annual_income),
                    "current_balance": money(current_balance),
                }
            )
            loan_number += 1

    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_ground_truth(path: Path, rows: list[dict[str, str]]) -> None:
    active = [row for row in rows if row["application_status"] == "Active"]
    current_balance = sum(float(row["current_balance"]) for row in active)
    average_lvr = sum(float(row["lvr_pct"]) for row in active) / len(active)

    state_balance: defaultdict[str, float] = defaultdict(float)
    for row in active:
        state_balance[row["state"]] += float(row["current_balance"])
    top_state, top_state_balance = max(state_balance.items(), key=lambda item: item[1])

    first_home_buyers = sum(row["first_home_buyer"] == "true" for row in active)
    arrears_count = sum(int(row["arrears_days"]) > 0 for row in active)
    arrears_30_count = sum(int(row["arrears_days"]) >= 30 for row in active)
    high_lvr_balance = sum(
        float(row["current_balance"])
        for row in active
        if float(row["lvr_pct"]) >= 80
    )

    decisioned = [
        row
        for row in rows
        if row["application_status"] in {"Active", "Approved", "Declined"}
    ]
    channel_days: defaultdict[str, list[int]] = defaultdict(list)
    for row in decisioned:
        channel_days[row["channel"]].append(int(row["days_to_decision"]))
    channel_averages = {
        channel: sum(values) / len(values) for channel, values in channel_days.items()
    }
    fastest_channel, fastest_days = min(
        channel_averages.items(), key=lambda item: item[1]
    )

    settlement_months = Counter(
        row["settlement_date"][:7] for row in active if row["settlement_date"]
    )
    top_month, top_month_count = max(
        settlement_months.items(), key=lambda item: (item[1], item[0])
    )

    evaluation_rows = [
        (
            "What is the current portfolio balance for active home loans?",
            f"AUD {current_balance:,.2f}",
        ),
        (
            "How many active home loans are in the portfolio?",
            f"{len(active)} active loans",
        ),
        (
            "What is the average LVR for active loans?",
            f"{average_lvr:.2f}%",
        ),
        (
            "Which state has the largest current portfolio balance?",
            f"{top_state} - AUD {top_state_balance:,.2f}",
        ),
        (
            "What percentage of active loans are first home buyers?",
            f"{first_home_buyers / len(active) * 100:.2f}% "
            f"({first_home_buyers} of {len(active)})",
        ),
        (
            "What is the arrears rate across active loans?",
            f"{arrears_count / len(active) * 100:.2f}% "
            f"({arrears_count} of {len(active)})",
        ),
        (
            "How many active loans are 30 or more days in arrears?",
            f"{arrears_30_count} active loans",
        ),
        (
            "What is the total balance of active loans with LVR at or above 80%?",
            f"AUD {high_lvr_balance:,.2f}",
        ),
        (
            "Which channel has the fastest average decision time for decisioned applications?",
            f"{fastest_channel} - {fastest_days:.2f} days",
        ),
        (
            "Which settlement month had the most active loan originations?",
            f"{top_month} - {top_month_count} active loans",
        ),
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["question", "expected_answer"])
        writer.writerows(evaluation_rows)


def main() -> None:
    rows = generate_rows()
    write_csv(DATA_PATH, rows)
    write_ground_truth(GROUND_TRUTH_PATH, rows)
    print(f"Wrote {len(rows)} rows to {DATA_PATH}")
    print(f"Wrote ground truth to {GROUND_TRUTH_PATH}")


if __name__ == "__main__":
    main()

