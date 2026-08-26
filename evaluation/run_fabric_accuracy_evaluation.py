#!/usr/bin/env python3
"""Run the native Fabric data agent accuracy evaluation."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from fabric.dataagent.evaluation import (
    evaluate_data_agent,
    get_evaluation_details,
    get_evaluation_summary,
)


ROOT = Path(__file__).resolve().parents[1]
AGENT_NAME = os.getenv("FABRIC_DATA_AGENT_NAME", "HomeLoansDataAgent")
WORKSPACE_NAME = os.getenv("FABRIC_WORKSPACE_NAME") or None
TABLE_NAME = os.getenv("FABRIC_EVALUATION_TABLE", "home_loans_agent_evaluation")
STAGE = os.getenv("FABRIC_DATA_AGENT_STAGE", "production")


def main() -> None:
    test_data = pd.read_csv(ROOT / "evaluation/ground_truth.csv")
    evaluation_id = evaluate_data_agent(
        test_data,
        AGENT_NAME,
        workspace_name=WORKSPACE_NAME,
        table_name=TABLE_NAME,
        data_agent_stage=STAGE,
    )
    print(f"Evaluation ID: {evaluation_id}")
    print(get_evaluation_summary(TABLE_NAME, verbose=True))
    details = get_evaluation_details(
        evaluation_id,
        TABLE_NAME,
        get_all_rows=True,
        verbose=True,
    )
    print(details)


if __name__ == "__main__":
    main()

