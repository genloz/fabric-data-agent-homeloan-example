#!/usr/bin/env python3
"""Create, configure, validate, and publish the Fabric home loans data agent."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from azure.identity import AzureCliCredential
from fabric.analytics.environment.credentials import (
    SetFabricAnalyticsDefaultTokenCredentialsGlobally,
)
from fabric.dataagent.client import create_data_agent


ROOT = Path(__file__).resolve().parents[1]
AGENT_NAME = os.getenv("FABRIC_DATA_AGENT_NAME", "HomeLoansDataAgent")
EXPECTED_TABLE = "home_loans"

AGENT_INSTRUCTIONS = json.loads(
    (
        ROOT
        / "fabric/HomeLoansDataAgent.DataAgent/Files/Config/draft/stage_config.json"
    ).read_text(encoding="utf-8")
)["aiInstructions"]
FEW_SHOTS = json.loads(
    (
        ROOT
        / "fabric/HomeLoansDataAgent.DataAgent/Files/Config/draft/"
        "lakehouse-HomeLoansLakehouse/fewshots.json"
    ).read_text(encoding="utf-8")
)["fewShots"]


def load_ids() -> tuple[str, str]:
    output_path = ROOT / "deployment/deployment-output.json"
    if output_path.exists():
        output = json.loads(output_path.read_text(encoding="utf-8"))
        return output["workspace_id"], output["lakehouse_id"]
    return os.environ["FABRIC_WORKSPACE_ID"], os.environ["FABRIC_LAKEHOUSE_ID"]


def items(page: Any) -> list[Any]:
    if isinstance(page, dict):
        return page.get("value") or page.get("elements") or page.get("items") or []
    if isinstance(page, (list, tuple)):
        return list(page)
    return []


def attr(element: Any, *names: str) -> Any:
    for name in names:
        if isinstance(element, dict) and name in element:
            return element[name]
        if hasattr(element, name):
            return getattr(element, name)
    return None


def get_elements(datasource: Any, root_id: str | None) -> list[Any]:
    output: list[Any] = []
    continuation_token = None
    while True:
        page = None
        attempts = (
            {"root_id": root_id, "continuation_token": continuation_token},
            {"root_id": root_id},
            {"parent_id": root_id},
        )
        for kwargs in attempts:
            try:
                page = datasource.get_elements(**kwargs)
                break
            except TypeError:
                continue
        if page is None:
            page = datasource.get_elements()
        output.extend(items(page))
        continuation_token = (
            page.get("continuationToken") if isinstance(page, dict) else None
        )
        if not continuation_token:
            return output


def select_table(datasource: Any, table_name: str) -> int:
    selected = 0
    stack: list[str | None] = [None]
    seen: set[str] = set()
    while stack:
        root_id = stack.pop()
        for element in get_elements(datasource, root_id):
            element_id = attr(element, "id")
            if element_id is None or str(element_id) in seen:
                continue
            seen.add(str(element_id))
            element_type = str(attr(element, "type") or "").lower()
            display_name = str(
                attr(element, "display_name", "displayName", "name") or ""
            )
            has_children = bool(attr(element, "hasSubElements", "has_sub_elements"))

            if element_type.endswith(".table") or element_type == "table":
                should_select = display_name.lower() == table_name.lower()
                try:
                    datasource.update_element(element_id, is_selected=should_select)
                except TypeError:
                    datasource.update_element(
                        element_id, {"isSelected": should_select}
                    )
                if should_select:
                    selected += 1
            elif has_children:
                stack.append(str(element_id))
    return selected


def main() -> None:
    workspace_id, lakehouse_id = load_ids()
    credential = AzureCliCredential()
    SetFabricAnalyticsDefaultTokenCredentialsGlobally(credential)

    print(f"Creating data agent: {AGENT_NAME}")
    agent = create_data_agent(
        data_agent_name=AGENT_NAME,
        workspace_id=workspace_id,
    )
    agent.update_settings(ai_instructions=AGENT_INSTRUCTIONS)
    agent.add_staging_datasource(
        artifact_name_or_id=lakehouse_id,
        workspace_id_or_name=workspace_id,
    )

    selected = 0
    datasource = None
    for attempt in range(18):
        datasources = list(agent.list_datasources())
        if datasources:
            datasource = datasources[0]
            selected = select_table(datasource, EXPECTED_TABLE)
            if selected:
                break
        if attempt == 0:
            print("Waiting for the lakehouse schema to finish syncing...")
        time.sleep(5)
    if not selected or datasource is None:
        raise RuntimeError(
            f"Could not select the {EXPECTED_TABLE} table after schema synchronization."
        )

    examples = {item["question"]: item["query"] for item in FEW_SHOTS}
    datasource.add_fewshots(examples)
    print(f"Added {len(examples)} example queries.")

    if os.getenv("VALIDATE_FEWSHOTS", "false").lower() == "true":
        result = datasource.evaluate_few_shots(batch_size=20)
        print(
            "Example query validation: "
            f"{result.success_count}/{result.total_examples} passed "
            f"({result.success_rate:.2f}%)."
        )
        if result.success_count != result.total_examples:
            raise RuntimeError("One or more example queries failed validation.")

    agent.publish_staging(
        description=(
            "Home Loans Portfolio Analyst: governed, read-only analytics over "
            "synthetic Australian home loans data."
        )
    )
    print(f"Published {AGENT_NAME}.")
    print(
        "Publish it to the Microsoft 365 Agent Store from the Fabric portal, "
        "then grant users access to both the agent and HomeLoansLakehouse."
    )


if __name__ == "__main__":
    main()

