#!/usr/bin/env python3
"""Create the Lakehouse, ingestion notebook, and Data Pipeline in Fabric."""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from azure.identity import AzureCliCredential


ROOT = Path(__file__).resolve().parents[1]
FABRIC_API = "https://api.fabric.microsoft.com/v1"
WORKSPACE_ID = os.environ["FABRIC_WORKSPACE_ID"]
RAW_CSV_URL = os.environ["GITHUB_RAW_CSV_URL"]

LAKEHOUSE_NAME = "HomeLoansLakehouse"
NOTEBOOK_NAME = "LoadHomeLoans"
PIPELINE_NAME = "IngestHomeLoans"


class FabricApi:
    def __init__(self) -> None:
        credential = AzureCliCredential()
        token = credential.get_token("https://api.fabric.microsoft.com/.default")
        self.headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
        }

    def request(
        self,
        method: str,
        url: str,
        *,
        body: dict[str, Any] | None = None,
        expected: tuple[int, ...] = (200, 201, 202),
    ) -> requests.Response:
        response = requests.request(
            method,
            url,
            headers=self.headers,
            json=body,
            timeout=(15, 120),
        )
        if response.status_code not in expected:
            detail = response.text[:1000]
            raise RuntimeError(
                f"Fabric request failed with HTTP {response.status_code}: {detail}"
            )
        return response

    def list_items(self) -> list[dict[str, Any]]:
        url = f"{FABRIC_API}/workspaces/{WORKSPACE_ID}/items"
        items: list[dict[str, Any]] = []
        while url:
            response = self.request("GET", url, expected=(200,))
            payload = response.json()
            items.extend(payload.get("value", []))
            url = payload.get("continuationUri")
        return items

    def find_item(self, display_name: str, item_type: str) -> dict[str, Any] | None:
        for item in self.list_items():
            if item.get("displayName") == display_name and item.get("type") == item_type:
                return item
        return None

    def create_item(
        self,
        display_name: str,
        description: str,
        item_type: str,
        definition: dict[str, Any],
    ) -> dict[str, Any]:
        response = self.request(
            "POST",
            f"{FABRIC_API}/workspaces/{WORKSPACE_ID}/items",
            body={
                "displayName": display_name,
                "description": description,
                "type": item_type,
                "definition": definition,
            },
        )
        if response.status_code in {200, 201}:
            return response.json()

        location = response.headers.get("Location")
        if not location:
            raise RuntimeError("Fabric returned an asynchronous operation without a URL.")
        operation = self.poll_operation(location)
        item_id = operation.get("resourceId") or operation.get("result", {}).get("id")
        if not item_id:
            item = self.find_item(display_name, item_type)
            if not item:
                raise RuntimeError(f"Created {display_name}, but its item ID was not found.")
            return item
        return {
            "id": item_id.rsplit("/", 1)[-1],
            "displayName": display_name,
            "type": item_type,
            "workspaceId": WORKSPACE_ID,
        }

    def get_or_create_item(
        self,
        display_name: str,
        description: str,
        item_type: str,
        definition: dict[str, Any],
    ) -> dict[str, Any]:
        existing = self.find_item(display_name, item_type)
        if existing:
            print(f"Reusing {item_type}: {display_name} ({existing['id']})")
            return existing
        print(f"Creating {item_type}: {display_name}")
        return self.create_item(display_name, description, item_type, definition)

    def poll_operation(self, location: str) -> dict[str, Any]:
        for _ in range(120):
            response = self.request("GET", location, expected=(200, 202))
            if response.status_code == 202:
                time.sleep(int(response.headers.get("Retry-After", "5")))
                continue
            payload = response.json()
            status = str(payload.get("status", "")).lower()
            if status in {"failed", "cancelled"}:
                raise RuntimeError(f"Fabric operation ended with status {status}: {payload}")
            if status in {"succeeded", "completed"} or not status:
                return payload
            time.sleep(5)
        raise TimeoutError("Timed out waiting for the Fabric operation.")

    def run_pipeline(self, pipeline_id: str) -> None:
        response = self.request(
            "POST",
            (
                f"{FABRIC_API}/workspaces/{WORKSPACE_ID}/items/{pipeline_id}"
                "/jobs/instances?jobType=Pipeline"
            ),
            body={"executionData": {"pipelineName": PIPELINE_NAME}},
            expected=(200, 202),
        )
        location = response.headers.get("Location")
        if not location:
            print("Pipeline run was accepted. Monitor it from the Fabric workspace.")
            return
        print("Waiting for the ingestion pipeline to finish...")
        self.poll_operation(location)
        print("Ingestion pipeline completed.")


def inline_part(path: str, content: str) -> dict[str, str]:
    return {
        "path": path,
        "payload": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "payloadType": "InlineBase64",
    }


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def lakehouse_definition() -> dict[str, Any]:
    return {
        "format": "LakehouseDefinitionV1",
        "parts": [
            inline_part(
                "lakehouse.metadata.json",
                read_text(
                    "fabric/HomeLoansLakehouse.Lakehouse/lakehouse.metadata.json"
                ),
            ),
            inline_part(
                "alm.settings.json",
                read_text("fabric/HomeLoansLakehouse.Lakehouse/alm.settings.json"),
            ),
            inline_part(
                ".platform", read_text("fabric/HomeLoansLakehouse.Lakehouse/.platform")
            ),
        ],
    }


def notebook_definition() -> dict[str, Any]:
    return {
        "format": "FabricGitSource",
        "parts": [
            inline_part(
                "notebook-content.py",
                read_text("fabric/LoadHomeLoans.Notebook/notebook-content.py"),
            ),
            inline_part(
                ".platform", read_text("fabric/LoadHomeLoans.Notebook/.platform")
            ),
        ],
    }


def pipeline_definition(
    notebook_id: str, lakehouse_id: str
) -> tuple[dict[str, Any], str]:
    template = read_text(
        "fabric/IngestHomeLoans.DataPipeline/pipeline-content.template.json"
    )
    rendered = (
        template.replace("<NOTEBOOK_ID>", notebook_id)
        .replace("<WORKSPACE_ID>", WORKSPACE_ID)
        .replace("<LAKEHOUSE_ID>", lakehouse_id)
        .replace("<RAW_CSV_URL>", RAW_CSV_URL)
    )
    json.loads(rendered)
    rendered_path = (
        ROOT / "fabric/IngestHomeLoans.DataPipeline/pipeline-content.json"
    )
    rendered_path.write_text(rendered + "\n", encoding="utf-8")
    return (
        {
            "parts": [
                inline_part("pipeline-content.json", rendered),
                inline_part(
                    ".platform",
                    read_text("fabric/IngestHomeLoans.DataPipeline/.platform"),
                ),
            ]
        },
        rendered,
    )


def main() -> None:
    api = FabricApi()
    lakehouse = api.get_or_create_item(
        LAKEHOUSE_NAME,
        "Synthetic Australian home loans portfolio for a Fabric data agent demo.",
        "Lakehouse",
        lakehouse_definition(),
    )
    notebook = api.get_or_create_item(
        NOTEBOOK_NAME,
        "Loads the GitHub home loans CSV into a Delta table.",
        "Notebook",
        notebook_definition(),
    )
    pipeline_payload, _ = pipeline_definition(notebook["id"], lakehouse["id"])
    pipeline = api.get_or_create_item(
        PIPELINE_NAME,
        "Orchestrates ingestion of the synthetic home loans CSV.",
        "DataPipeline",
        pipeline_payload,
    )

    deployment_output = {
        "workspace_id": WORKSPACE_ID,
        "lakehouse_id": lakehouse["id"],
        "notebook_id": notebook["id"],
        "pipeline_id": pipeline["id"],
        "raw_csv_url": RAW_CSV_URL,
    }
    output_path = ROOT / "deployment/deployment-output.json"
    output_path.write_text(json.dumps(deployment_output, indent=2) + "\n")
    print(json.dumps(deployment_output, indent=2))
    api.run_pipeline(pipeline["id"])
    print("Next: run deployment/configure_data_agent.py.")


if __name__ == "__main__":
    main()

