#!/usr/bin/env python3
"""Evaluate the Foundry wrapper agent with quality and responsible AI evaluators."""

from __future__ import annotations

import os
import time
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import TestingCriterionAzureAIEvaluator
from azure.identity import DefaultAzureCredential
from openai.types.eval_create_params import DataSourceConfigCustom


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
MODEL_DEPLOYMENT = os.environ["FOUNDRY_MODEL_DEPLOYMENT_NAME"]
AGENT_NAME = os.environ["FOUNDRY_AGENT_NAME"]


def criterion(
    name: str,
    evaluator_name: str,
    data_mapping: dict[str, str],
    *,
    judge_model: bool = False,
) -> TestingCriterionAzureAIEvaluator:
    kwargs = {
        "type": "azure_ai_evaluator",
        "name": name,
        "evaluator_name": evaluator_name,
        "data_mapping": data_mapping,
    }
    if judge_model:
        kwargs["initialization_parameters"] = {"deployment_name": MODEL_DEPLOYMENT}
    return TestingCriterionAzureAIEvaluator(**kwargs)


def main() -> None:
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )
    client = project_client.get_openai_client()
    dataset = project_client.datasets.upload_file(
        name="home-loans-rai-queries",
        version=os.getenv("EVALUATION_DATASET_VERSION", "1"),
        file_path=str(ROOT / "foundry/rai_agent_queries.jsonl"),
    )

    query_response = {
        "query": "{{item.query}}",
        "response": "{{sample.output_text}}",
    }
    agent_mapping = {
        "query": "{{item.query}}",
        "response": "{{sample.output_items}}",
        "tool_calls": "{{sample.tool_calls}}",
    }
    testing_criteria = [
        criterion(
            "Coherence",
            "builtin.coherence",
            query_response,
            judge_model=True,
        ),
        criterion("Hate and Unfairness", "builtin.hate_unfairness", query_response),
        criterion("Violence", "builtin.violence", query_response),
        criterion("Self Harm", "builtin.self_harm", query_response),
        criterion(
            "Prohibited Actions",
            "builtin.prohibited_actions",
            agent_mapping,
        ),
        criterion(
            "Sensitive Data Leakage",
            "builtin.sensitive_data_leakage",
            agent_mapping,
        ),
    ]

    data_source_config = DataSourceConfigCustom(
        type="custom",
        item_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        include_sample_schema=True,
    )
    evaluation = client.evals.create(
        name="Home Loans Responsible AI Evaluation",
        data_source_config=data_source_config,
        testing_criteria=testing_criteria,
    )
    target = {
        "type": "azure_ai_agent",
        "name": AGENT_NAME,
    }
    agent_version = os.getenv("FOUNDRY_AGENT_VERSION")
    if agent_version:
        target["version"] = agent_version

    eval_run = client.evals.runs.create(
        eval_id=evaluation.id,
        name="Home Loans Agent Evaluation Run",
        data_source={
            "type": "azure_ai_target_completions",
            "source": {"type": "file_id", "id": dataset.id},
            "input_messages": {
                "type": "template",
                "template": [
                    {
                        "type": "message",
                        "role": "user",
                        "content": {
                            "type": "input_text",
                            "text": "{{item.query}}",
                        },
                    }
                ],
            },
            "target": target,
        },
    )
    while True:
        run = client.evals.runs.retrieve(
            run_id=eval_run.id,
            eval_id=evaluation.id,
        )
        if run.status in {"completed", "failed"}:
            break
        time.sleep(10)
    print(f"Status: {run.status}")
    print(f"Report URL: {run.report_url}")
    if run.status != "completed":
        raise SystemExit("Foundry evaluation did not complete successfully.")


if __name__ == "__main__":
    main()
