#!/usr/bin/env python3
"""Validate the generated repository without external dependencies."""

from __future__ import annotations

import csv
import json
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate_json() -> None:
    for path in ROOT.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    for path in ROOT.rglob("*.jsonl"):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.strip():
                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    raise AssertionError(
                        f"Invalid JSONL in {path} at line {line_number}: {exc}"
                    ) from exc


def validate_python() -> None:
    for path in ROOT.rglob("*.py"):
        py_compile.compile(str(path), doraise=True)


def validate_csv() -> None:
    data_path = ROOT / "data/home_loans.csv"
    with data_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 360:
        raise AssertionError(f"Expected 360 sample rows, found {len(rows)}.")
    loan_ids = [row["loan_id"] for row in rows]
    if len(set(loan_ids)) != len(loan_ids):
        raise AssertionError("loan_id values must be unique.")
    if any(
        row["state"] not in {"NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"}
        for row in rows
    ):
        raise AssertionError("Unexpected state value.")
    if any(float(row["lvr_pct"]) <= 0 or float(row["lvr_pct"]) > 100 for row in rows):
        raise AssertionError("LVR values must be between 0 and 100.")
    if any(
        row["application_status"] not in {"Active", "Approved", "Declined", "Withdrawn"}
        for row in rows
    ):
        raise AssertionError("Unexpected application_status value.")

    ground_truth_path = ROOT / "evaluation/ground_truth.csv"
    with ground_truth_path.open(encoding="utf-8", newline="") as handle:
        ground_truth = list(csv.DictReader(handle))
    if len(ground_truth) < 10:
        raise AssertionError("At least 10 ground-truth questions are required.")


def validate_required_files() -> None:
    required = [
        "README.md",
        "data/home_loans.csv",
        "fabric/HomeLoansLakehouse.Lakehouse/lakehouse.metadata.json",
        "fabric/LoadHomeLoans.Notebook/notebook-content.py",
        "fabric/IngestHomeLoans.DataPipeline/pipeline-content.template.json",
        "fabric/HomeLoansDataAgent.DataAgent/Files/Config/draft/stage_config.json",
        "deployment/templates/home_loans_datasource.template.json",
        "deployment/templates/home_loans_fewshots.json",
        "evaluation/rai_test_cases.jsonl",
        "m365/sample_questions.md",
        "foundry/README.md",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    if missing:
        raise AssertionError(f"Missing required files: {missing}")


def validate_fabric_data_agent() -> None:
    draft_path = (
        ROOT
        / "fabric/HomeLoansDataAgent.DataAgent/Files/Config/draft"
    )
    invalid_templates = list(draft_path.rglob("*.template.json"))
    if invalid_templates:
        raise AssertionError(
            "Fabric Data Agent item definitions cannot contain datasource templates: "
            f"{invalid_templates}"
        )

    for path in draft_path.iterdir():
        if path.is_dir() and any(path.iterdir()) and not path.name.startswith(
            ("lakehouse-tables-", "warehouse-tables-", "semantic-model-", "kusto-", "ontology-")
        ):
            raise AssertionError(f"Invalid Fabric Data Agent data source folder: {path}")


def main() -> None:
    validate_json()
    validate_python()
    validate_csv()
    validate_required_files()
    validate_fabric_data_agent()
    print("Repository validation passed.")


if __name__ == "__main__":
    main()
